# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import json
import threading
from typing import Any, Dict, Optional

from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest
from datetime import datetime

from UM.Job import Job
from UM.Logger import Logger
from UM.Message import Message
from UM.TaskManagement.HttpRequestManager import HttpRequestManager
from UM.TaskManagement.HttpRequestScope import JsonDecoratorScope

from UM.i18n import i18nCatalog
from cura.CuraApplication import CuraApplication
from plugins.Toolbox.src.UltimakerCloudScope import UltimakerCloudScope

catalog = i18nCatalog("cura")


class CreateBackupJob(Job):
    """Creates backup zip, requests upload url and uploads the backup file to cloud storage."""

    MESSAGE_TITLE = catalog.i18nc("@info:title", "Backups")

    def __init__(self, api_backup_url: str) -> None:
        """ Create a new backup Job. start the job by calling start()

        :param api_backup_url: The url of the 'backups' endpoint of the Cura Drive Api
        """

        super().__init__()

        self._api_backup_url = api_backup_url
        self._jsonCloudScope = JsonDecoratorScope(UltimakerCloudScope(CuraApplication.getInstance()))


        self._backup_zip = None
        self._upload_success = False
        self._upload_success_available = threading.Event()
        self.backup_upload_error_message = ""

    def run(self) -> None:
        upload_message = Message(catalog.i18nc("@info:backup_status", "Creating your backup..."), title = self.MESSAGE_TITLE, progress = -1)
        upload_message.show()
        CuraApplication.getInstance().processEvents()
        cura_api = CuraApplication.getInstance().getCuraAPI()
        self._backup_zip, backup_meta_data = cura_api.backups.createBackup()

        if not self._backup_zip or not backup_meta_data:
            self.backup_upload_error_message = "Could not create backup."
            upload_message.hide()
            return

        upload_message.setText(catalog.i18nc("@info:backup_status", "Uploading your backup..."))
        CuraApplication.getInstance().processEvents()

        # Create an upload entry for the backup.
        timestamp = datetime.now().isoformat()
        backup_meta_data["description"] = "{}.backup.{}.cura.zip".format(timestamp, backup_meta_data["cura_release"])
        self._requestUploadSlot(backup_meta_data, len(self._backup_zip))

        self._upload_success_available.wait()
        upload_message.hide()

    def _requestUploadSlot(self, backup_metadata: Dict[str, Any], backup_size: int) -> None:
        """Request a backup upload slot from the API.

        :param backup_metadata: A dict containing some meta data about the backup.
        :param backup_size: The size of the backup file in bytes.
        :return: The upload URL for the actual backup file if successful, otherwise None.
        """

        payload = json.dumps({"data": {"backup_size": backup_size,
                                       "metadata": backup_metadata
                                       }
                              }).encode()

        HttpRequestManager.getInstance().put(
            self._api_backup_url,
            data = payload,
            callback = self._onUploadSlotCompleted,
            error_callback = self._onUploadSlotCompleted,
            scope = self._jsonCloudScope)

    def _onUploadSlotCompleted(self, reply: QNetworkReply, error: Optional["QNetworkReply.NetworkError"] = None) -> None:
        if error is not None:
            Logger.warning(str(error))
            self.backup_upload_error_message = "Could not upload backup."
            self._upload_success_available.set()
            return
        if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) >= 300:
            Logger.warning("Could not request backup upload: %s", HttpRequestManager.readText(reply))
            self.backup_upload_error_message = "Could not upload backup."
            self._upload_success_available.set()
            return

        backup_upload_url = HttpRequestManager.readJSON(reply)["data"]["upload_url"]

        # Upload the backup to storage.
        HttpRequestManager.getInstance().put(
            backup_upload_url,
            data=self._backup_zip,
            callback=self._uploadFinishedCallback,
            error_callback=self._uploadFinishedCallback
        )

    def _uploadFinishedCallback(self, reply: QNetworkReply, error: QNetworkReply.NetworkError = None):
        self.backup_upload_error_text = HttpRequestManager.readText(reply)

        if HttpRequestManager.replyIndicatesSuccess(reply, error):
            self._upload_success = True
            Message(catalog.i18nc("@info:backup_status", "Your backup has finished uploading."), title = self.MESSAGE_TITLE).show()
        else:
            self.backup_upload_error_text = self.backup_upload_error_text
            Logger.log("w", "Could not upload backup file: %s", self.backup_upload_error_text)
            Message(catalog.i18nc("@info:backup_status", "There was an error while uploading your backup."),
                    title=self.MESSAGE_TITLE).show()

        self._upload_success_available.set()
