# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from PyQt5.QtNetwork import QNetworkReply

from UM.Job import Job
from UM.Logger import Logger
from UM.Message import Message
from UM.TaskManagement.HttpRequestManager import HttpRequestManager

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


class UploadBackupJob(Job):
    MESSAGE_TITLE = catalog.i18nc("@info:title", "Backups")

    # This job is responsible for uploading the backup file to cloud storage.
    # As it can take longer than some other tasks, we schedule this using a Cura Job.
    def __init__(self, signed_upload_url: str, backup_zip: bytes) -> None:
        super().__init__()
        self._signed_upload_url = signed_upload_url
        self._backup_zip = backup_zip
        self._upload_success = False
        self.backup_upload_error_text = ""
        self._message = None

    def run(self) -> None:
        self._message = Message(catalog.i18nc("@info:backup_status", "Uploading your backup..."), title = self.MESSAGE_TITLE, progress = -1)
        self._message.show()

        HttpRequestManager.getInstance().put(
            self._signed_upload_url, 
            data = self._backup_zip
        )

    def uploadFinishedCallback(self, reply: QNetworkReply, error: QNetworkReply.NetworkError):
        self._message.hide()

        self.backup_upload_error_text = HttpRequestManager.readText(reply)

        if HttpRequestManager.replyIndicatesSuccess(reply, error):
            self._upload_success = True
            Message(catalog.i18nc("@info:backup_status", "Your backup has finished uploading."), title = self.MESSAGE_TITLE).show()
        else:
            self.backup_upload_error_text = self.backup_upload_error_text
            Logger.log("w", "Could not upload backup file: %s", self.backup_upload_error_text)
            Message(catalog.i18nc("@info:backup_status", "There was an error while uploading your backup."),
                    title=self.MESSAGE_TITLE).show()

        self.finished.emit(self)
