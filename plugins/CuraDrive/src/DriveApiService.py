# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import base64
import hashlib
from tempfile import NamedTemporaryFile
from typing import Any, Optional, List, Dict, Callable

from UM.Logger import Logger
from UM.Signal import Signal, signalemitter
from UM.TaskManagement.HttpRequestManager import HttpRequestManager
from UM.TaskManagement.HttpRequestScope import JsonDecoratorScope
from cura.CuraApplication import CuraApplication
from plugins.Toolbox.src.UltimakerCloudScope import UltimakerCloudScope

from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest

from .CreateBackupJob import CreateBackupJob
from .Settings import Settings

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


@signalemitter
class DriveApiService:
    """The DriveApiService is responsible for interacting with the CuraDrive API and Cura's backup handling."""

    BACKUP_URL = "{}/backups".format(Settings.DRIVE_API_URL)
    DISK_WRITE_BUFFER_SIZE = 512 * 1024

    restoringStateChanged = Signal()
    """Emits signal when restoring backup started or finished."""

    creatingStateChanged = Signal()
    """Emits signal when creating backup started or finished."""

    def __init__(self) -> None:
        self._cura_api = CuraApplication.getInstance().getCuraAPI()
        self._jsonCloudScope = JsonDecoratorScope(UltimakerCloudScope(CuraApplication.getInstance()))

    def getBackups(self, changed: Callable[[List], None]):
        def callback(reply: QNetworkReply, error: Optional["QNetworkReply.NetworkError"] = None):
            if error is not None:
                Logger.log("w", "Could not get backups: " + str(error))
                changed([])
                return

            backup_list_response = HttpRequestManager.readJSON(reply)
            if "data" not in backup_list_response:
                Logger.log("w", "Could not get backups from remote, actual response body was: %s",
                           str(backup_list_response))
                changed([])  # empty list of backups
                return

            changed(backup_list_response["data"])

        HttpRequestManager.getInstance().get(
            self.BACKUP_URL,
            callback= callback,
            error_callback = callback,
            scope=self._jsonCloudScope
        )

    def createBackup(self) -> None:
        self.creatingStateChanged.emit(is_creating = True)
        upload_backup_job = CreateBackupJob(self.BACKUP_URL)
        upload_backup_job.finished.connect(self._onUploadFinished)
        upload_backup_job.start()

    def _onUploadFinished(self, job: "CreateBackupJob") -> None:
        if job.backup_upload_error_message != "":
            # If the job contains an error message we pass it along so the UI can display it.
            self.creatingStateChanged.emit(is_creating = False, error_message = job.backup_upload_error_message)
        else:
            self.creatingStateChanged.emit(is_creating = False)

    def restoreBackup(self, backup: Dict[str, Any]) -> None:
        self.restoringStateChanged.emit(is_restoring = True)
        download_url = backup.get("download_url")
        if not download_url:
            # If there is no download URL, we can't restore the backup.
            return self._emitRestoreError()

        def finishedCallback(reply: QNetworkReply, bu=backup) -> None:
            self._onRestoreRequestCompleted(reply, None, bu)

        HttpRequestManager.getInstance().get(
            url = download_url,
            callback = finishedCallback,
            error_callback = self._onRestoreRequestCompleted
        )

    def _onRestoreRequestCompleted(self, reply: QNetworkReply, error: Optional["QNetworkReply.NetworkError"] = None, backup = None):
        if not HttpRequestManager.replyIndicatesSuccess(reply, error):
            Logger.log("w",
                       "Requesting backup failed, response code %s while trying to connect to %s",
                       reply.attribute(QNetworkRequest.HttpStatusCodeAttribute), reply.url())
            self._emitRestoreError()
            return

        # We store the file in a temporary path fist to ensure integrity.
        temporary_backup_file = NamedTemporaryFile(delete = False)
        with open(temporary_backup_file.name, "wb") as write_backup:
            app = CuraApplication.getInstance()
            bytes_read = reply.read(DriveApiService.DISK_WRITE_BUFFER_SIZE)
            while bytes_read:
                write_backup.write(bytes_read)
                bytes_read = reply.read(DriveApiService.DISK_WRITE_BUFFER_SIZE)
                app.processEvents()

        if not self._verifyMd5Hash(temporary_backup_file.name, backup.get("md5_hash", "")):
            # Don't restore the backup if the MD5 hashes do not match.
            # This can happen if the download was interrupted.
            Logger.log("w", "Remote and local MD5 hashes do not match, not restoring backup.")
            return self._emitRestoreError()

        # Tell Cura to place the backup back in the user data folder.
        with open(temporary_backup_file.name, "rb") as read_backup:
            self._cura_api.backups.restoreBackup(read_backup.read(), backup.get("metadata", {}))
            self.restoringStateChanged.emit(is_restoring = False)

    def _emitRestoreError(self) -> None:
        self.restoringStateChanged.emit(is_restoring = False,
                                        error_message = catalog.i18nc("@info:backup_status",
                                                                         "There was an error trying to restore your backup."))

    @staticmethod
    def _verifyMd5Hash(file_path: str, known_hash: str) -> bool:
        """Verify the MD5 hash of a file.

        :param file_path: Full path to the file.
        :param known_hash: The known MD5 hash of the file.
        :return: Success or not.
        """

        with open(file_path, "rb") as read_backup:
            local_md5_hash = base64.b64encode(hashlib.md5(read_backup.read()).digest(), altchars = b"_-").decode("utf-8")
            return known_hash == local_md5_hash

    def deleteBackup(self, backup_id: str, finishedCallable: Callable[[bool], None]):

        def finishedCallback(reply: QNetworkReply, ca=finishedCallable) -> None:
            self._onDeleteRequestCompleted(reply, None, ca)

        def errorCallback(reply: QNetworkReply, error: QNetworkReply.NetworkError, ca=finishedCallable) -> None:
            self._onDeleteRequestCompleted(reply, error, ca)

        HttpRequestManager.getInstance().delete(
            url = "{}/{}".format(self.BACKUP_URL, backup_id),
            callback = finishedCallback,
            error_callback = errorCallback,
            scope= self._jsonCloudScope
        )

    def _onDeleteRequestCompleted(self, reply: QNetworkReply, error: Optional["QNetworkReply.NetworkError"] = None, callable = None):
        callable(HttpRequestManager.replyIndicatesSuccess(reply, error))
