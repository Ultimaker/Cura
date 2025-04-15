# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.
import json
import threading
from datetime import datetime
from typing import Any, Dict, Optional

from PyQt6.QtNetwork import QNetworkReply

from UM.Job import Job
from UM.Logger import Logger
from UM.Message import Message
from UM.TaskManagement.HttpRequestManager import HttpRequestManager
from UM.TaskManagement.HttpRequestScope import JsonDecoratorScope
from UM.i18n import i18nCatalog
from cura.ApplicationMetadata import CuraSDKVersion
from cura.CuraApplication import CuraApplication
from cura.UltimakerCloud.UltimakerCloudScope import UltimakerCloudScope
import cura.UltimakerCloud.UltimakerCloudConstants as UltimakerCloudConstants

catalog = i18nCatalog("cura")

PACKAGES_URL = f"{UltimakerCloudConstants.CuraCloudAPIRoot}/cura-packages/v{UltimakerCloudConstants.CuraCloudAPIVersion}/cura/v{CuraSDKVersion}/packages"

class CreateBackupJob(Job):
    """Creates backup zip, requests upload url and uploads the backup file to cloud storage."""

    MESSAGE_TITLE = catalog.i18nc("@info:title", "Backups")
    DEFAULT_UPLOAD_ERROR_MESSAGE = catalog.i18nc("@info:backup_status", "There was an error while uploading your backup.")

    def __init__(self, api_backup_url: str) -> None:
        """ Create a new backup Job. start the job by calling start()

        :param api_backup_url: The url of the 'backups' endpoint of the Cura Drive Api
        """

        super().__init__()

        self._api_backup_url = api_backup_url
        self._json_cloud_scope = JsonDecoratorScope(UltimakerCloudScope(CuraApplication.getInstance()))

        self._backup_zip = None  # type: Optional[bytes]
        self._job_done = threading.Event()
        """Set when the job completes. Does not indicate success."""
        self.backup_upload_error_message = ""
        """After the job completes, an empty string indicates success. Otherwise, the value is a translated message."""

    def _setPluginFetchErrorMessage(self, error_msg: str) -> None:
        Logger.error(f"Fetching plugins for backup resulted in error: {error_msg}")
        self.backup_upload_error_message = "Couldn't update currently available plugins, backup stopped."
        self._upload_message.hide()
        self._job_done.set()

    def run(self) -> None:
        self._upload_message = Message(catalog.i18nc("@info:backup_status", "Fetch re-downloadable package-ids..."),
                                 title = self.MESSAGE_TITLE,
                                 progress = -1)
        self._upload_message.show()
        CuraApplication.getInstance().processEvents()

        if CuraApplication.getInstance().getCuraAPI().backups.shouldReinstallDownloadablePlugins():
            request_url = f"{PACKAGES_URL}?package_type=plugin"
            scope = JsonDecoratorScope(UltimakerCloudScope(CuraApplication.getInstance()))
            HttpRequestManager.getInstance().get(
                request_url,
                scope=scope,
                callback=self._continueRun,
                error_callback=lambda reply, error: self._setPluginFetchErrorMessage(str(error)),
            )
        else:
            self._continueRun()

    def _continueRun(self, reply: "QNetworkReply" = None) -> None:
        if reply is not None:
            response_data = HttpRequestManager.readJSON(reply)
            if "data" not in response_data:
                self._setPluginFetchErrorMessage(f"Missing 'data' from response. Keys in response: {response_data.keys()}")
                return
            available_remote_plugins = frozenset({v["package_id"] for v in response_data["data"]})
        else:
            available_remote_plugins = frozenset()

        self._upload_message.setText(catalog.i18nc("@info:backup_status", "Creating your backup..."))
        CuraApplication.getInstance().processEvents()
        cura_api = CuraApplication.getInstance().getCuraAPI()
        self._backup_zip, backup_meta_data = cura_api.backups.createBackup(available_remote_plugins)

        if not self._backup_zip or not backup_meta_data:
            self.backup_upload_error_message = catalog.i18nc("@info:backup_status", "There was an error while creating your backup.")
            self._upload_message.hide()
            return

        self._upload_message.setText(catalog.i18nc("@info:backup_status", "Uploading your backup..."))
        CuraApplication.getInstance().processEvents()

        # Create an upload entry for the backup.
        timestamp = datetime.now().isoformat()
        backup_meta_data["description"] = "{}.backup.{}.cura.zip".format(timestamp, backup_meta_data["cura_release"])
        self._requestUploadSlot(backup_meta_data, len(self._backup_zip))

        # Note: One 'process events' call wasn't enough with the changed situation somehow.
        for _ in range(5000):
            CuraApplication.getInstance().processEvents()
            if self._job_done.wait(0.02):
                break

        if self.backup_upload_error_message == "":
            self._upload_message.setText(catalog.i18nc("@info:backup_status", "Your backup has finished uploading."))
            self._upload_message.setProgress(None)  # Hide progress bar
        else:
            # some error occurred. This error is presented to the user by DrivePluginExtension
            self._upload_message.hide()

    def _requestUploadSlot(self, backup_metadata: Dict[str, Any], backup_size: int) -> None:
        """Request a backup upload slot from the API.

        :param backup_metadata: A dict containing some meta data about the backup.
        :param backup_size: The size of the backup file in bytes.
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
            scope = self._json_cloud_scope)

    def _onUploadSlotCompleted(self, reply: QNetworkReply, error: Optional["QNetworkReply.NetworkError"] = None) -> None:
        if HttpRequestManager.safeHttpStatus(reply) >= 300:
            replyText = HttpRequestManager.readText(reply)
            Logger.warning("Could not request backup upload: %s", replyText)
            self.backup_upload_error_message = self.DEFAULT_UPLOAD_ERROR_MESSAGE

            if HttpRequestManager.safeHttpStatus(reply) == 400:
                errors = json.loads(replyText)["errors"]
                if "moreThanMaximum" in [error["code"] for error in errors if error["meta"] and error["meta"]["field_name"] == "backup_size"]:
                    self.backup_upload_error_message = catalog.i18nc("@error:file_size", "The backup exceeds the maximum file size.")

            self._job_done.set()
            return

        if error is not None:
            Logger.warning("Could not request backup upload: %s", HttpRequestManager.qt_network_error_name(error))
            self.backup_upload_error_message = self.DEFAULT_UPLOAD_ERROR_MESSAGE
            self._job_done.set()
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
        if not HttpRequestManager.replyIndicatesSuccess(reply, error):
            Logger.log("w", "Could not upload backup file: %s", HttpRequestManager.readText(reply))
            self.backup_upload_error_message = self.DEFAULT_UPLOAD_ERROR_MESSAGE

        self._job_done.set()
