# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import json, os
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

from UM.Extension import Extension
from UM.Application import Application
from UM.Logger import Logger
from UM.PluginRegistry import PluginRegistry
from UM.i18n import i18nCatalog
from UM.Settings.ContainerRegistry import ContainerRegistry

from cura.Settings.GlobalStack import GlobalStack

from .FirmwareUpdateCheckerJob import FirmwareUpdateCheckerJob, get_settings_key_for_machine

i18n_catalog = i18nCatalog("cura")

## This Extension checks for new versions of the firmware based on the latest checked version number.
#  The plugin is currently only usable for applications maintained by Ultimaker. But it should be relatively easy
#  to change it to work for other applications.
class FirmwareUpdateChecker(Extension):

    def __init__(self):
        super().__init__()

        # Listen to a Signal that indicates a change in the list of printers, just if the user has enabled the
        # 'check for updates' option
        Application.getInstance().getPreferences().addPreference("info/automatic_update_check", True)
        if Application.getInstance().getPreferences().getValue("info/automatic_update_check"):
            ContainerRegistry.getInstance().containerAdded.connect(self._onContainerAdded)

        self._late_init = True  # Init some things after creation, since we need the path from the plugin-mgr.
        self._download_url = None
        self._check_job = None
        self._name_cache = []

    ##  Callback for the message that is spawned when there is a new version.
    # TODO: Set the right download URL for each message!
    def _onActionTriggered(self, message, action):
        if action == "download":
            if self._download_url is not None:
                QDesktopServices.openUrl(QUrl(self._download_url))

    def _onSetDownloadUrl(self, download_url):
        self._download_url = download_url

    def _onContainerAdded(self, container):
        # Only take care when a new GlobalStack was added
        if isinstance(container, GlobalStack):
            self.checkFirmwareVersion(container, True)

    def _onJobFinished(self, *args, **kwargs):
        self._check_job = None

    def lateInit(self):
        self._late_init = False

        # Open the .json file with the needed lookup-lists for each machine(/model) and retrieve 'raw' json.
        self._machines_json = None
        json_path = os.path.join(PluginRegistry.getInstance().getPluginPath("FirmwareUpdateChecker"),
                                 "resources/machines.json")
        with open(json_path, "r", encoding="utf-8") as json_file:
            self._machines_json = json.load(json_file).get("machines")
        if self._machines_json is None:
            Logger.log('e', "Missing or inaccessible: {0}".format(json_path))
            return

        # Initialize the Preference called `latest_checked_firmware` that stores the last version
        # checked for each printer.
        for machine_json in self._machines_json:
            machine_id = machine_json.get("id")
            Application.getInstance().getPreferences().addPreference(get_settings_key_for_machine(machine_id), "")

    ##  Connect with software.ultimaker.com, load latest.version and check version info.
    #   If the version info is different from the current version, spawn a message to
    #   allow the user to download it.
    #
    #   \param silent type(boolean) Suppresses messages other than "new version found" messages.
    #                               This is used when checking for a new firmware version at startup.
    def checkFirmwareVersion(self, container = None, silent = False):
        if self._late_init:
            self.lateInit()

        container_name = container.definition.getName()
        if container_name in self._name_cache:
            return
        self._name_cache.append(container_name)

        self._check_job = FirmwareUpdateCheckerJob(container = container, silent = silent,
                                                   machines_json = self._machines_json,
                                                   callback = self._onActionTriggered,
                                                   set_download_url_callback = self._onSetDownloadUrl)
        self._check_job.start()
        self._check_job.finished.connect(self._onJobFinished)
