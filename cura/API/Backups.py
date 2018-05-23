# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from cura.Backups.BackupsManager import BackupsManager


class Backups:
    """
    The backups API provides a version-proof bridge between Cura's BackupManager and plugins that hook into it.

    Usage:
        from cura.API import CuraAPI
        api = CuraAPI()
        api.backups.createBackup()
        api.backups.restoreBackup(my_zip_file, {"cura_release": "3.1"})
    """

    manager = BackupsManager()  # Re-used instance of the backups manager.

    def createBackup(self) -> (bytes, dict):
        """
        Create a new backup using the BackupsManager.
        :return: Tuple containing a ZIP file with the backup data and a dict with meta data about the backup.
        """
        return self.manager.createBackup()

    def restoreBackup(self, zip_file: bytes, meta_data: dict) -> None:
        """
        Restore a backup using the BackupManager.
        :param zip_file: A ZIP file containing the actual backup data.
        :param meta_data: Some meta data needed for restoring a backup, like the Cura version number.
        """
        return self.manager.restoreBackup(zip_file, meta_data)
