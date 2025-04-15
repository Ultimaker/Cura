# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.
import base64
import hashlib
import json
import os
import threading
from tempfile import NamedTemporaryFile
from typing import Optional, Any, Dict

from PyQt6.QtNetwork import QNetworkReply, QNetworkRequest

from UM.Job import Job
from UM.Logger import Logger
from UM.PackageManager import catalog
from UM.Resources import Resources
from UM.TaskManagement.HttpRequestManager import HttpRequestManager
from UM.Version import Version

from cura.ApplicationMetadata import CuraSDKVersion
from cura.CuraApplication import CuraApplication
from cura.UltimakerCloud.UltimakerCloudScope import UltimakerCloudScope
import cura.UltimakerCloud.UltimakerCloudConstants as UltimakerCloudConstants

PACKAGES_URL_TEMPLATE = f"{UltimakerCloudConstants.CuraCloudAPIRoot}/cura-packages/v{UltimakerCloudConstants.CuraCloudAPIVersion}/cura/v{{0}}/packages/{{1}}/download"

class RestoreBackupJob(Job):
    """Downloads a backup and overwrites local configuration with the backup.

     When `Job.finished` emits, `restore_backup_error_message` will either be `""` (no error) or an error message
     """

    DISK_WRITE_BUFFER_SIZE = 512 * 1024
    DEFAULT_ERROR_MESSAGE = catalog.i18nc("@info:backup_status", "There was an error trying to restore your backup.")

    def __init__(self, backup: Dict[str, Any]) -> None:
        """ Create a new restore Job. start the job by calling start()

        :param backup: A dict containing a backup spec
        """

        super().__init__()
        self._job_done = threading.Event()

        self._backup = backup
        self.restore_backup_error_message = ""

    def run(self) -> None:
        url = self._backup.get("download_url")
        assert url is not None

        HttpRequestManager.getInstance().get(
            url = url,
            callback = self._onRestoreRequestCompleted,
            error_callback = self._onRestoreRequestCompleted
        )

        # Note: Just to be sure, use the same structure here as in CreateBackupJob.
        for _ in range(5000):
            CuraApplication.getInstance().processEvents()
            if self._job_done.wait(0.02):
                break

    def _onRestoreRequestCompleted(self, reply: QNetworkReply, error: Optional["QNetworkReply.NetworkError"] = None) -> None:
        if not HttpRequestManager.replyIndicatesSuccess(reply, error):
            Logger.warning("Requesting backup failed, response code %s while trying to connect to %s",
                           reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute), reply.url())
            self.restore_backup_error_message = self.DEFAULT_ERROR_MESSAGE
            self._job_done.set()
            return

        # We store the file in a temporary path fist to ensure integrity.
        try:
            self._temporary_backup_file = NamedTemporaryFile(delete_on_close = False)
            with open(self._temporary_backup_file.name, "wb") as write_backup:
                app = CuraApplication.getInstance()
                bytes_read = reply.read(self.DISK_WRITE_BUFFER_SIZE)
                while bytes_read:
                    write_backup.write(bytes_read)
                    bytes_read = reply.read(self.DISK_WRITE_BUFFER_SIZE)
                    app.processEvents()
        except EnvironmentError as e:
            Logger.error(f"Unable to save backed up files due to computer limitations: {str(e)}")
            self.restore_backup_error_message = self.DEFAULT_ERROR_MESSAGE
            self._job_done.set()
            return

        if not self._verifyMd5Hash(self._temporary_backup_file.name, self._backup.get("md5_hash", "")):
            # Don't restore the backup if the MD5 hashes do not match.
            # This can happen if the download was interrupted.
            Logger.error("Remote and local MD5 hashes do not match, not restoring backup.")
            self.restore_backup_error_message = self.DEFAULT_ERROR_MESSAGE
            self._job_done.set()
            return

        # Tell Cura to place the backup back in the user data folder.
        metadata = self._backup.get("metadata", {})
        with open(self._temporary_backup_file.name, "rb") as read_backup:
            cura_api = CuraApplication.getInstance().getCuraAPI()
            cura_api.backups.restoreBackup(read_backup.read(), metadata, auto_close=False)

        # Read packages data-file, to get the 'to_install' plugin-ids.
        version_to_restore = Version(metadata.get("cura_release", "dev"))
        version_str = f"{version_to_restore.getMajor()}.{version_to_restore.getMinor()}"
        packages_path = os.path.abspath(os.path.join(os.path.abspath(
            Resources.getConfigStoragePath()), "..", version_str, "packages.json"))
        if not os.path.exists(packages_path):
            Logger.error(f"Can't find path '{packages_path}' to tell what packages should be redownloaded.")
            self.restore_backup_error_message = self.DEFAULT_ERROR_MESSAGE
            self._job_done.set()
            return

        to_install = {}
        try:
            with open(packages_path, "r") as packages_file:
                packages_json = json.load(packages_file)
                if "to_install" in packages_json:
                    for package_data in packages_json["to_install"].values():
                        if "package_info" not in package_data:
                            continue
                        package_info = package_data["package_info"]
                        if "package_id" in package_info and "sdk_version_semver" in package_info:
                            to_install[package_info["package_id"]] = package_info["sdk_version_semver"]
        except IOError as ex:
            Logger.error(f"Couldn't open '{packages_path}' because '{str(ex)}' to get packages to re-install.")
            self.restore_backup_error_message = self.DEFAULT_ERROR_MESSAGE
            self._job_done.set()
            return

        if len(to_install) < 1:
            Logger.info("No packages to reinstall, early out.")
            self._job_done.set()
            return

        # Download all re-installable plugins packages, so they can be put back on start-up.
        redownload_errors = []
        def packageDownloadCallback(package_id: str, msg: "QNetworkReply", err: "QNetworkReply.NetworkError" = None) -> None:
            if err is not None or HttpRequestManager.safeHttpStatus(msg) != 200:
                redownload_errors.append(err)
            del to_install[package_id]

            try:
                with NamedTemporaryFile(mode="wb", suffix=".curapackage", delete=False) as temp_file:
                    bytes_read = msg.read(self.DISK_WRITE_BUFFER_SIZE)
                    while bytes_read:
                        temp_file.write(bytes_read)
                        bytes_read = msg.read(self.DISK_WRITE_BUFFER_SIZE)
                        CuraApplication.getInstance().processEvents()
                temp_file.close()
                if not CuraApplication.getInstance().getPackageManager().installPackage(temp_file.name):
                    redownload_errors.append(f"Couldn't install package '{package_id}'.")
            except IOError as ex:
                redownload_errors.append(f"Couldn't process package '{package_id}' because '{ex}'.")

            if len(to_install) < 1:
                if len(redownload_errors) == 0:
                    Logger.info("All packages redownloaded!")
                    self._job_done.set()
                else:
                    msgs = "\n - ".join(redownload_errors)
                    Logger.error(f"Couldn't re-install at least one package(s) because: {msgs}")
                    self.restore_backup_error_message = self.DEFAULT_ERROR_MESSAGE
                    self._job_done.set()

        self._package_download_scope = UltimakerCloudScope(CuraApplication.getInstance())
        for package_id, package_api_version in to_install.items():
            def handlePackageId(package_id: str = package_id):
                HttpRequestManager.getInstance().get(
                    PACKAGES_URL_TEMPLATE.format(package_api_version, package_id),
                    scope=self._package_download_scope,
                    callback=lambda msg: packageDownloadCallback(package_id, msg),
                    error_callback=lambda msg, err: packageDownloadCallback(package_id, msg, err)
                )
            handlePackageId(package_id)

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
