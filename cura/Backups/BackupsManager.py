# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Dict, Optional, Tuple, TYPE_CHECKING

from UM.Logger import Logger
from cura.Backups.Backup import Backup

if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication


##  The BackupsManager is responsible for managing the creating and restoring of
#   back-ups.
#
#   Back-ups themselves are represented in a different class.
class BackupsManager:
    def __init__(self, application: "CuraApplication") -> None:
        self._application = application

    ##  Get a back-up of the current configuration.
    #   \return A tuple containing a ZipFile (the actual back-up) and a dict
    #   containing some metadata (like version).
    def createBackup(self) -> Tuple[Optional[bytes], Optional[Dict[str, str]]]:
        self._disableAutoSave()
        backup = Backup(self._application)
        backup.makeFromCurrent()
        self._enableAutoSave()
        # We don't return a Backup here because we want plugins only to interact with our API and not full objects.
        return backup.zip_file, backup.meta_data

    ##  Restore a back-up from a given ZipFile.
    #   \param zip_file A bytes object containing the actual back-up.
    #   \param meta_data A dict containing some metadata that is needed to
    #   restore the back-up correctly.
    def restoreBackup(self, zip_file: bytes, meta_data: Dict[str, str]) -> None:
        if not meta_data.get("cura_release", None):
            # If there is no "cura_release" specified in the meta data, we don't execute a backup restore.
            Logger.log("w", "Tried to restore a backup without specifying a Cura version number.")
            return

        self._disableAutoSave()

        backup = Backup(self._application, zip_file = zip_file, meta_data = meta_data)
        restored = backup.restore()
        if restored:
            # At this point, Cura will need to restart for the changes to take effect.
            # We don't want to store the data at this point as that would override the just-restored backup.
            self._application.windowClosed(save_data = False)

    ##  Here we try to disable the auto-save plug-in as it might interfere with
    #   restoring a back-up.
    def _disableAutoSave(self) -> None:
        self._application.setSaveDataEnabled(False)

    ##  Re-enable auto-save after we're done.
    def _enableAutoSave(self) -> None:
        self._application.setSaveDataEnabled(True)
