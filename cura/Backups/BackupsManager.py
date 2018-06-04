# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional

from UM.Logger import Logger
from cura.Backups.Backup import Backup
from cura.CuraApplication import CuraApplication


class BackupsManager:
    """
    The BackupsManager is responsible for managing the creating and restoring of backups.
    Backups themselves are represented in a different class.
    """
    def __init__(self):
        self._application = CuraApplication.getInstance()

    def createBackup(self) -> (Optional[bytes], Optional[dict]):
        """
        Get a backup of the current configuration.
        :return: A Tuple containing a ZipFile (the actual backup) and a dict containing some meta data (like version).
        """
        self._disableAutoSave()
        backup = Backup()
        backup.makeFromCurrent()
        self._enableAutoSave()
        # We don't return a Backup here because we want plugins only to interact with our API and not full objects.
        return backup.zip_file, backup.meta_data

    def restoreBackup(self, zip_file: bytes, meta_data: dict) -> None:
        """
        Restore a backup from a given ZipFile.
        :param zip_file: A bytes object containing the actual backup.
        :param meta_data: A dict containing some meta data that is needed to restore the backup correctly.
        """
        if not meta_data.get("cura_release", None):
            # If there is no "cura_release" specified in the meta data, we don't execute a backup restore.
            Logger.log("w", "Tried to restore a backup without specifying a Cura version number.")
            return

        self._disableAutoSave()

        backup = Backup(zip_file = zip_file, meta_data = meta_data)
        restored = backup.restore()
        if restored:
            # At this point, Cura will need to restart for the changes to take effect.
            # We don't want to store the data at this point as that would override the just-restored backup.
            self._application.windowClosed(save_data=False)

    def _disableAutoSave(self):
        """Here we try to disable the auto-save plugin as it might interfere with restoring a backup."""
        self._application.setSaveDataEnabled(False)

    def _enableAutoSave(self):
        """Re-enable auto-save after we're done."""
        self._application.setSaveDataEnabled(True)
