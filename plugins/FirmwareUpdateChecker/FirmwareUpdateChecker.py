# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

from UM.Extension import Extension
from UM.Preferences import Preferences
from UM.Logger import Logger
from UM.i18n import i18nCatalog
from cura.Settings.GlobalStack import GlobalStack

from .FirmwareUpdateCheckerJob import FirmwareUpdateCheckerJob
from UM.Settings.ContainerRegistry import ContainerRegistry

i18n_catalog = i18nCatalog("cura")


## This Extension checks for new versions of the firmware based on the latest checked version number.
#  The plugin is currently only usable for applications maintained by Ultimaker. But it should be relatively easy
#  to change it to work for other applications.
class FirmwareUpdateChecker(Extension):
    JEDI_VERSION_URL = "http://software.ultimaker.com/jedi/releases/latest.version"

    def __init__(self):
        super().__init__()

        # Initialize the Preference called `latest_checked_firmware` that stores the last version
        # checked for the UM3. In the future if we need to check other printers' firmware
        Preferences.getInstance().addPreference("info/latest_checked_firmware", "")

        # Listen to a Signal that indicates a change in the list of printers, just if the user has enabled the
        # 'check for updates' option
        Preferences.getInstance().addPreference("info/automatic_update_check", True)
        if Preferences.getInstance().getValue("info/automatic_update_check"):
            ContainerRegistry.getInstance().containerAdded.connect(self._onContainerAdded)

        self._download_url = None

    ##  Callback for the message that is spawned when there is a new version.
    def _onActionTriggered(self, message, action):
        if action == "download":
            if self._download_url is not None:
                QDesktopServices.openUrl(QUrl(self._download_url))

    def _onSetDownloadUrl(self, download_url):
        self._download_url = download_url

    def _onContainerAdded(self, container):
        # Only take care when a new GlobalStack was added
        if isinstance(container, GlobalStack):
            Logger.log("i", "You have a '%s' in printer list. Let's check the firmware!", container.getId())
            self.checkFirmwareVersion(container, True)

    ##  Connect with software.ultimaker.com, load latest.version and check version info.
    #   If the version info is different from the current version, spawn a message to
    #   allow the user to download it.
    #
    #   \param silent type(boolean) Suppresses messages other than "new version found" messages.
    #                               This is used when checking for a new firmware version at startup.
    def checkFirmwareVersion(self, container = None, silent = False):
        job = FirmwareUpdateCheckerJob(container = container, silent = silent, url = self.JEDI_VERSION_URL,
                                       callback = self._onActionTriggered,
                                       set_download_url_callback = self._onSetDownloadUrl)
        job.start()
