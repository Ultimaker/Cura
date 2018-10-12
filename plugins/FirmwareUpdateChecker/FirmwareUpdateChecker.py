# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

from typing import List

from UM.Extension import Extension
from UM.Application import Application
from UM.Logger import Logger
from UM.PluginRegistry import PluginRegistry
from UM.i18n import i18nCatalog
from UM.Settings.ContainerRegistry import ContainerRegistry

from cura.Settings.GlobalStack import GlobalStack

from .FirmwareUpdateCheckerJob import FirmwareUpdateCheckerJob
from .FirmwareUpdateCheckerLookup import FirmwareUpdateCheckerLookup, get_settings_key_for_machine

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

        self._late_init = True  # Init some things after creation, since we need the path from the plugin-mgr.
        self._download_url = None
        self._check_job = None
        self._name_cache = []  # type: List[str]
        self._lookups = None

    ##  Callback for the message that is spawned when there is a new version.
    def _onActionTriggered(self, message, action):
        try:
            download_url = self._lookups.getRedirectUserFor(int(action))
            if download_url is not None:
                QDesktopServices.openUrl(QUrl(download_url))
            else:
                Logger.log("e", "Can't find URL for {0}".format(action))
        except Exception as ex:
            Logger.log("e", "Don't know what to do with '{0}' because {1}".format(action, ex))

    def _onContainerAdded(self, container):
        # Only take care when a new GlobalStack was added
        if isinstance(container, GlobalStack):
            self.checkFirmwareVersion(container, True)

    def _onJobFinished(self, *args, **kwargs):
        self._check_job = None

    def doLateInit(self):
        self._late_init = False

        self._lookups = FirmwareUpdateCheckerLookup(os.path.join(PluginRegistry.getInstance().getPluginPath(
            "FirmwareUpdateChecker"), "resources/machines.json"))

        # Initialize the Preference called `latest_checked_firmware` that stores the last version
        # checked for each printer.
        for machine_id in self._lookups.getMachineIds():
            Application.getInstance().getPreferences().addPreference(get_settings_key_for_machine(machine_id), "")

    ##  Connect with software.ultimaker.com, load latest.version and check version info.
    #   If the version info is different from the current version, spawn a message to
    #   allow the user to download it.
    #
    #   \param silent type(boolean) Suppresses messages other than "new version found" messages.
    #                               This is used when checking for a new firmware version at startup.
    def checkFirmwareVersion(self, container = None, silent = False):
        if self._late_init:
            self.doLateInit()

        container_name = container.definition.getName()
        if container_name in self._name_cache:
            return
        self._name_cache.append(container_name)

        self._check_job = FirmwareUpdateCheckerJob(container = container, silent = silent,
                                                   lookups = self._lookups,
                                                   callback = self._onActionTriggered)
        self._check_job.start()
        self._check_job.finished.connect(self._onJobFinished)
