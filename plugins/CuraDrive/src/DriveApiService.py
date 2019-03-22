# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import base64
import hashlib
from datetime import datetime
from tempfile import NamedTemporaryFile
from typing import Any, Optional, List, Dict

import requests

from UM.Logger import Logger
from UM.Message import Message
from UM.Signal import Signal, signalemitter
from cura.CuraApplication import CuraApplication

from .UploadBackupJob import UploadBackupJob
from .Settings import Settings

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


## The DriveApiService is responsible for interacting with the CuraDrive API and Cura's backup handling.
@signalemitter
class DriveApiService:
    BACKUP_URL = "{}/backups".format(Settings.DRIVE_API_URL)

    # Emit signal when restoring backup started or finished.
    restoringStateChanged = Signal()

    # Emit signal when creating backup started or finished.
    creatingStateChanged = Signal()

    def __init__(self) -> None:
        self._cura_api = CuraApplication.getInstance().getCuraAPI()

    def getBackups(self) -> List[Dict[str, Any]]:
        access_token = self._cura_api.account.accessToken
        if not access_token:
            Logger.log("w", "Could not get access token.")
            return []
        try:
            backup_list_request = requests.get(self.BACKUP_URL, headers = {
                "Authorization": "Bearer {}".format(access_token)
            })
        except requests.exceptions.ConnectionError:
            Logger.log("w", "Unable to connect with the server.")
            return []

        # HTTP status 300s mean redirection. 400s and 500s are errors.
        # Technically 300s are not errors, but the use case here relies on "requests" to handle redirects automatically.
        if backup_list_request.status_code >= 300:
            Logger.log("w", "Could not get backups list from remote: %s", backup_list_request.text)
            Message(catalog.i18nc("@info:backup_status", "There was an error listing your backups."), title = catalog.i18nc("@info:title", "Backup")).show()
            return []

        backup_list_response = backup_list_request.json()
        if "data" not in backup_list_response:
            Logger.log("w", "Could not get backups from remote, actual response body was: %s", str(backup_list_response))
            return []

        return backup_list_response["data"]

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
        backup_upload_url = self._requestBackupUpload(backup_meta_data, len(backup_zip_file))
        if not backup_upload_url:
            self.creatingStateChanged.emit(is_creating = False, error_message ="Could not upload backup.")
            return

        # Upload the backup to storage.
        upload_backup_job = UploadBackupJob(backup_upload_url, backup_zip_file)
        upload_backup_job.finished.connect(self._onUploadFinished)
        upload_backup_job.start()

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

        download_package = requests.get(download_url, stream = True)
        if download_package.status_code >= 300:
            # Something went wrong when attempting to download the backup.
            Logger.log("w", "Could not download backup from url %s: %s", download_url, download_package.text)
            return self._emitRestoreError()

        # We store the file in a temporary path fist to ensure integrity.
        temporary_backup_file = NamedTemporaryFile(delete = False)
        with open(temporary_backup_file.name, "wb") as write_backup:
            for chunk in download_package:
                write_backup.write(chunk)

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

    #   Verify the MD5 hash of a file.
    #   \param file_path Full path to the file.
    #   \param known_hash The known MD5 hash of the file.
    #   \return: Success or not.
    @staticmethod
    def _verifyMd5Hash(file_path: str, known_hash: str) -> bool:
        with open(file_path, "rb") as read_backup:
            local_md5_hash = base64.b64encode(hashlib.md5(read_backup.read()).digest(), altchars = b"_-").decode("utf-8")
            return known_hash == local_md5_hash

    def deleteBackup(self, backup_id: str) -> bool:
        access_token = self._cura_api.account.accessToken
        if not access_token:
            Logger.log("w", "Could not get access token.")
            return False

        delete_backup = requests.delete("{}/{}".format(self.BACKUP_URL, backup_id), headers = {
            "Authorization": "Bearer {}".format(access_token)
        })
        if delete_backup.status_code >= 300:
            Logger.log("w", "Could not delete backup: %s", delete_backup.text)
            return False
        return True

    #   Request a backup upload slot from the API.
    #   \param backup_metadata: A dict containing some meta data about the backup.
    #   \param backup_size The size of the backup file in bytes.
    #   \return: The upload URL for the actual backup file if successful, otherwise None.
    def _requestBackupUpload(self, backup_metadata: Dict[str, Any], backup_size: int) -> Optional[str]:
        access_token = self._cura_api.account.accessToken
        if not access_token:
            Logger.log("w", "Could not get access token.")
            return None
        
        backup_upload_request = requests.put(self.BACKUP_URL, json = {
            "data": {
                "backup_size": backup_size,
                "metadata": backup_metadata
            }
        }, headers = {
            "Authorization": "Bearer {}".format(access_token)
        })

        # Any status code of 300 or above indicates an error.
        if backup_upload_request.status_code >= 300:
            Logger.log("w", "Could not request backup upload: %s", backup_upload_request.text)
            return None
        
        return backup_upload_request.json()["data"]["upload_url"]
