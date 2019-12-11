# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

from typing import Set

from UM.Extension import Extension
from UM.Application import Application
from UM.Logger import Logger
from UM.i18n import i18nCatalog
from UM.Settings.ContainerRegistry import ContainerRegistry

from .FirmwareUpdateCheckerJob import FirmwareUpdateCheckerJob
from .FirmwareUpdateCheckerMessage import FirmwareUpdateCheckerMessage

i18n_catalog = i18nCatalog("cura")


## This Extension checks for new versions of the firmware based on the latest checked version number.
#  The plugin is currently only usable for applications maintained by Ultimaker. But it should be relatively easy
#  to change it to work for other applications.
class FirmwareUpdateChecker(Extension):

    def __init__(self) -> None:
        super().__init__()

        # Listen to a Signal that indicates a change in the list of printers, just if the user has enabled the
        # "check for updates" option
        Application.getInstance().getPreferences().addPreference("info/automatic_update_check", True)
        if Application.getInstance().getPreferences().getValue("info/automatic_update_check"):
            ContainerRegistry.getInstance().containerAdded.connect(self._onContainerAdded)

        self._check_job = None
        self._checked_printer_names = set()  # type: Set[str]

    ##  Callback for the message that is spawned when there is a new version.
    def _onActionTriggered(self, message, action):
        if action == FirmwareUpdateCheckerMessage.STR_ACTION_DOWNLOAD:
            machine_id = message.getMachineId()
            download_url = message.getDownloadUrl()
            if download_url is not None:
                if QDesktopServices.openUrl(QUrl(download_url)):
                    Logger.log("i", "Redirected browser to {0} to show newly available firmware.".format(download_url))
                else:
                    Logger.log("e", "Can't reach URL: {0}".format(download_url))
            else:
                Logger.log("e", "Can't find URL for {0}".format(machine_id))

    def _onContainerAdded(self, container):
        # Only take care when a new GlobalStack was added
        from cura.Settings.GlobalStack import GlobalStack  # otherwise circular imports
        if isinstance(container, GlobalStack):
            self.checkFirmwareVersion(container, True)

    def _onJobFinished(self, *args, **kwargs):
        self._check_job = None

    ##  Connect with software.ultimaker.com, load latest.version and check version info.
    #   If the version info is different from the current version, spawn a message to
    #   allow the user to download it.
    #
    #   \param silent type(boolean) Suppresses messages other than "new version found" messages.
    #                               This is used when checking for a new firmware version at startup.
    def checkFirmwareVersion(self, container = None, silent = False):
        container_name = container.definition.getName()
        if container_name in self._checked_printer_names:
            return
        self._checked_printer_names.add(container_name)

        metadata = container.definition.getMetaData().get("firmware_update_info")
        if metadata is None:
            Logger.log("i", "No machine with name {0} in list of firmware to check.".format(container_name))
            return

        self._check_job = FirmwareUpdateCheckerJob(silent = silent,
                                                   machine_name = container_name, metadata = metadata,
                                                   callback = self._onActionTriggered)
        self._check_job.start()
        self._check_job.finished.connect(self._onJobFinished)
