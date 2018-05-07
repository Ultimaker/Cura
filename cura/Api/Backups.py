# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from zipfile import ZipFile

from cura.Backups.BackupsManager import BackupsManager


class Backups:
    """
    The backups API provides a version-proof bridge between Cura's BackupManager and plugins that hook into it.

    Usage:
        cura.Api.backups.createBackup()
        cura.Api.backups.restoreBackup(my_zip_file, {"cura_release": "3.1"})
    """

    manager = BackupsManager()  # Re-used instance of the backups manager.

    def createBackup(self) -> ("ZipFile", dict):
        """
        Create a new backup using the BackupsManager.
        :return:
        """
        return self.manager.createBackup()

    def restoreBackup(self, zip_file: "ZipFile", meta_data: dict) -> None:
        return self.manager.restoreBackup(zip_file, meta_data)
