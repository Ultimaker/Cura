# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Tuple, Optional

from cura.Backups.BackupsManager import BackupsManager


##  The back-ups API provides a version-proof bridge between Cura's
#   BackupManager and plug-ins that hook into it.
#
#   Usage:
#       ``from cura.API import CuraAPI
#       api = CuraAPI()
#       api.backups.createBackup()
#       api.backups.restoreBackup(my_zip_file, {"cura_release": "3.1"})``

class Backups:
    manager = BackupsManager()  # Re-used instance of the backups manager.

    ##  Create a new back-up using the BackupsManager.
    #   \return Tuple containing a ZIP file with the back-up data and a dict
    #   with metadata about the back-up.
    def createBackup(self) -> Tuple[Optional[bytes], Optional[dict]]:
        return self.manager.createBackup()

    ##  Restore a back-up using the BackupsManager.
    #   \param zip_file A ZIP file containing the actual back-up data.
    #   \param meta_data Some metadata needed for restoring a back-up, like the
    #   Cura version number.
    def restoreBackup(self, zip_file: bytes, meta_data: dict) -> None:
        return self.manager.restoreBackup(zip_file, meta_data)
