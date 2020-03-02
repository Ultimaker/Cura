# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import base64
import hashlib
import json
from datetime import datetime
from tempfile import NamedTemporaryFile
from typing import Any, Optional, List, Dict, Callable

from UM.Logger import Logger
from UM.Signal import Signal, signalemitter
from UM.TaskManagement.HttpRequestManager import HttpRequestManager
from UM.TaskManagement.HttpRequestScope import JsonDecoratorScope
from cura.CuraApplication import CuraApplication
from plugins.Toolbox.src.UltimakerCloudScope import UltimakerCloudScope

from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest

from .UploadBackupJob import UploadBackupJob
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
        self._current_backup_zip_file = None

        self.creatingStateChanged.connect(self._creatingStateChanged)

    def getBackups(self, changed: Callable[[List], None]):
        def callback(reply: QNetworkReply, error: Optional["QNetworkReply.NetworkError"] = None):
            if error is not None:
                Logger.log("w", "Could not get backups: " + str(error))
                changed([])

            backup_list_response = HttpRequestManager.readJSON(reply)
            if "data" not in backup_list_response:
                Logger.log("w", "Could not get backups from remote, actual response body was: %s",
                           str(backup_list_response))
                changed([])  # empty list of backups

            changed(backup_list_response["data"])

        HttpRequestManager.getInstance().get(
            self.BACKUP_URL,
            callback= callback,
            error_callback = callback,
            scope=self._jsonCloudScope
        )

    def createBackup(self) -> None:
        self.creatingStateChanged.emit(is_creating = True)

        # Create the backup.
        backup_zip_file, backup_meta_data = self._cura_api.backups.createBackup()
        if not backup_zip_file or not backup_meta_data:
            self.creatingStateChanged.emit(is_creating = False, error_message ="Could not create backup.")
            return

        # Create an upload entry for the backup.
        timestamp = datetime.now().isoformat()
        backup_meta_data["description"] = "{}.backup.{}.cura.zip".format(timestamp, backup_meta_data["cura_release"])
        self._requestBackupUpload(backup_meta_data, len(backup_zip_file))
        self._current_backup_zip_file = backup_zip_file

    def _onUploadFinished(self, job: "UploadBackupJob") -> None:
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

    def _requestBackupUpload(self, backup_metadata: Dict[str, Any], backup_size: int) -> None:
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
            self.BACKUP_URL,
            data = payload,
            callback = self._onBackupUploadSlotCompleted,
            error_callback = self._onBackupUploadSlotCompleted,
            scope = self._jsonCloudScope)

    def _onBackupUploadSlotCompleted(self, reply: QNetworkReply, error: Optional["QNetworkReply.NetworkError"] = None) -> None:
        if error is not None:
            Logger.warning(str(error))
            self.creatingStateChanged.emit(is_creating=False, error_message="Could not upload backup.")
            return
        if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) >= 300:
            Logger.warning("Could not request backup upload: %s", HttpRequestManager.readText(reply))
            self.creatingStateChanged.emit(is_creating=False, error_message="Could not upload backup.")
            return

        backup_upload_url = HttpRequestManager.readJSON(reply)["data"]["upload_url"]

        # Upload the backup to storage.
        upload_backup_job = UploadBackupJob(backup_upload_url, self._current_backup_zip_file)
        upload_backup_job.finished.connect(self._onUploadFinished)
        upload_backup_job.start()

    def _creatingStateChanged(self, is_creating: bool = False, error_message: str = None) -> None:
        """Cleanup after a backup is not needed anymore"""

        if not is_creating:
            self._current_backup_zip_file = None
