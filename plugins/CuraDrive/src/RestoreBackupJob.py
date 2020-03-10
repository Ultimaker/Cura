import base64
import hashlib
import threading
from tempfile import NamedTemporaryFile
from typing import Optional, Any, Dict

from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest

from UM.Job import Job
from UM.Logger import Logger
from UM.PackageManager import catalog
from UM.TaskManagement.HttpRequestManager import HttpRequestManager
from cura.CuraApplication import CuraApplication


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

    def run(self):

        HttpRequestManager.getInstance().get(
            url = self._backup.get("download_url"),
            callback = self._onRestoreRequestCompleted,
            error_callback = self._onRestoreRequestCompleted
        )

        self._job_done.wait()  # A job is considered finished when the run function completes

    def _onRestoreRequestCompleted(self, reply: QNetworkReply, error: Optional["QNetworkReply.NetworkError"] = None):
        if not HttpRequestManager.replyIndicatesSuccess(reply, error):
            Logger.warning("Requesting backup failed, response code %s while trying to connect to %s",
                           reply.attribute(QNetworkRequest.HttpStatusCodeAttribute), reply.url())
            self.restore_backup_error_message = self.DEFAULT_ERROR_MESSAGE
            self._job_done.set()
            return

        # We store the file in a temporary path fist to ensure integrity.
        temporary_backup_file = NamedTemporaryFile(delete = False)
        with open(temporary_backup_file.name, "wb") as write_backup:
            app = CuraApplication.getInstance()
            bytes_read = reply.read(self.DISK_WRITE_BUFFER_SIZE)
            while bytes_read:
                write_backup.write(bytes_read)
                bytes_read = reply.read(self.DISK_WRITE_BUFFER_SIZE)
                app.processEvents()

        if not self._verifyMd5Hash(temporary_backup_file.name, self._backup.get("md5_hash", "")):
            # Don't restore the backup if the MD5 hashes do not match.
            # This can happen if the download was interrupted.
            Logger.log("w", "Remote and local MD5 hashes do not match, not restoring backup.")
            self.restore_backup_error_message = self.DEFAULT_ERROR_MESSAGE

        # Tell Cura to place the backup back in the user data folder.
        with open(temporary_backup_file.name, "rb") as read_backup:
            cura_api = CuraApplication.getInstance().getCuraAPI()
            cura_api.backups.restoreBackup(read_backup.read(), self._backup.get("metadata", {}))

        self._job_done.set()

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
