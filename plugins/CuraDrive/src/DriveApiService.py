# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Optional, List, Dict, Callable

from PyQt5.QtNetwork import QNetworkReply

from UM.Logger import Logger
from UM.Signal import Signal, signalemitter
from UM.TaskManagement.HttpRequestManager import HttpRequestManager
from UM.TaskManagement.HttpRequestScope import JsonDecoratorScope
from UM.i18n import i18nCatalog
from cura.CuraApplication import CuraApplication
from cura.UltimakerCloud.UltimakerCloudScope import UltimakerCloudScope
from .CreateBackupJob import CreateBackupJob
from .RestoreBackupJob import RestoreBackupJob
from .Settings import Settings

catalog = i18nCatalog("cura")


@signalemitter
class DriveApiService:
    """The DriveApiService is responsible for interacting with the CuraDrive API and Cura's backup handling."""

    BACKUP_URL = "{}/backups".format(Settings.DRIVE_API_URL)

    restoringStateChanged = Signal()
    """Emits signal when restoring backup started or finished."""

    creatingStateChanged = Signal()
    """Emits signal when creating backup started or finished."""

    def __init__(self) -> None:
        self._cura_api = CuraApplication.getInstance().getCuraAPI()
        self._jsonCloudScope = JsonDecoratorScope(UltimakerCloudScope(CuraApplication.getInstance()))

    def getBackups(self, changed: Callable[[List[Dict[str, Any]]], None]) -> None:
        def callback(reply: QNetworkReply, error: Optional["QNetworkReply.NetworkError"] = None) -> None:
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
            Logger.warning("backup download_url is missing. Aborting backup.")
            self.restoringStateChanged.emit(is_restoring = False,
                                            error_message = catalog.i18nc("@info:backup_status",
                                                                        "There was an error trying to restore your backup."))
            return

        restore_backup_job = RestoreBackupJob(backup)
        restore_backup_job.finished.connect(self._onRestoreFinished)
        restore_backup_job.start()

    def _onRestoreFinished(self, job: "RestoreBackupJob"):
        if job.restore_backup_error_message != "":
            # If the job contains an error message we pass it along so the UI can display it.
            self.restoringStateChanged.emit(is_restoring=False)
        else:
            self.restoringStateChanged.emit(is_restoring = False, error_message = job.restore_backup_error_message)

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

    @staticmethod
    def _onDeleteRequestCompleted(reply: QNetworkReply, error: Optional["QNetworkReply.NetworkError"] = None, callable = None):
        callable(HttpRequestManager.replyIndicatesSuccess(reply, error))
