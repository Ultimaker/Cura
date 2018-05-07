# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from zipfile import ZipFile


class BackupsManager:
    """
    The BackupsManager is responsible for managing the creating and restoring of backups.
    Backups themselves are represented in a different class.
    """

    def __init__(self):
        pass

    def createBackup(self) -> ("ZipFile", dict):
        """
        Get a backup of the current configuration.
        :return: A Tuple containing a ZipFile (the actual backup) and a dict containing some meta data (like version).
        """
        pass

    def restoreBackup(self, zip_file: "ZipFile", meta_data: dict) -> None:
        """
        Restore a backup from a given ZipFile.
        :param zip_file: A ZipFile containing the actual backup.
        :param meta_data: A dict containing some meta data that is needed to restore the backup correctly.
        """
        pass
