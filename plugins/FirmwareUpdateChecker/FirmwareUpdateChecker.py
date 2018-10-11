# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

from UM.Extension import Extension
from UM.Application import Application
from UM.Logger import Logger
from UM.i18n import i18nCatalog
from UM.Settings.ContainerRegistry import ContainerRegistry

from cura.Settings.GlobalStack import GlobalStack

from .FirmwareUpdateCheckerJob import FirmwareUpdateCheckerJob, MachineId, get_settings_key_for_machine

i18n_catalog = i18nCatalog("cura")

## This Extension checks for new versions of the firmware based on the latest checked version number.
#  The plugin is currently only usable for applications maintained by Ultimaker. But it should be relatively easy
#  to change it to work for other applications.
class FirmwareUpdateChecker(Extension):
    JEDI_VERSION_URL = "http://software.ultimaker.com/jedi/releases/latest.version?utm_source=cura&utm_medium=software&utm_campaign=resources"
    UM_NEW_URL_TEMPLATE = "http://software.ultimaker.com/releases/firmware/{0}/stable/version.txt"
    VERSION_URLS_PER_MACHINE = \
        {
            MachineId.UM3: [JEDI_VERSION_URL, UM_NEW_URL_TEMPLATE.format(MachineId.UM3.value)],
            MachineId.UM3E: [JEDI_VERSION_URL, UM_NEW_URL_TEMPLATE.format(MachineId.UM3E.value)],
            MachineId.S5: [UM_NEW_URL_TEMPLATE.format(MachineId.S5.value)]
        }
    # The 'new'-style URL is the only way to check for S5 firmware,
    # and in the future, the UM3 line will also switch over, but for now the old 'JEDI'-style URL is still needed.
    # TODO: Parse all of that from a file, because this will be a big mess of large static values which gets worse with each printer.
    #       See also the to-do in FirmWareCheckerJob.

    def __init__(self):
        super().__init__()

        # Initialize the Preference called `latest_checked_firmware` that stores the last version
        # checked for each printer.
        for machine_id in MachineId:
            Application.getInstance().getPreferences().addPreference(get_settings_key_for_machine(machine_id), "")

        # Listen to a Signal that indicates a change in the list of printers, just if the user has enabled the
        # 'check for updates' option
        Application.getInstance().getPreferences().addPreference("info/automatic_update_check", True)
        if Application.getInstance().getPreferences().getValue("info/automatic_update_check"):
            ContainerRegistry.getInstance().containerAdded.connect(self._onContainerAdded)

        self._download_url = None
        self._check_job = None
        self._name_cache = []

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
        if container_name in self._name_cache:
            return
        self._name_cache.append(container_name)

        self._check_job = FirmwareUpdateCheckerJob(container = container, silent = silent,
                                                   urls = self.VERSION_URLS_PER_MACHINE,
                                                   callback = self._onActionTriggered,
                                                   set_download_url_callback = self._onSetDownloadUrl)
        self._check_job.start()
        self._check_job.finished.connect(self._onJobFinished)
