# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Extension import Extension
from UM.Preferences import Preferences
from UM.i18n import i18nCatalog

from .FirmwareUpdateCheckerJob import FirmwareUpdateCheckerJob

i18n_catalog = i18nCatalog("cura")


## This Extension checks for new versions of the firmware based on the latest checked version number.
#  The plugin is currently only usable for applications maintained by Ultimaker. But it should be relatively easy
#  to change it to work for other applications.
class FirmwareUpdateChecker(Extension):
    url = "http://software.ultimaker.com/jedi/releases/latest.version"

    def __init__(self):
        super().__init__()

        Preferences.getInstance().addPreference("info/latest_checked_firmware", "")
        self.checkFirmwareVersion(True)

    ##  Connect with software.ultimaker.com, load latest.version and check version info.
    #   If the version info is different from the current version, spawn a message to
    #   allow the user to download it.
    #
    #   \param silent type(boolean) Suppresses messages other than "new version found" messages.
    #                               This is used when checking for a new firmware version at startup.
    def checkFirmwareVersion(self, silent = False):
        job = FirmwareUpdateCheckerJob(silent = silent, url = self.url)
        job.start()