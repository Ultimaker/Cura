# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Preferences import Preferences
from UM.Application import Application
from UM.Message import Message
from UM.Logger import Logger
from UM.Job import Job

import urllib.request
import codecs

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices


from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")


##  This job checks if there is an update available on the provided URL.
class FirmwareUpdateCheckerJob(Job):
    def __init__(self, silent = False, url = None):
        super().__init__()
        self.silent = silent
        self._url = url
        self._download_url = None  # If an update was found, the download_url will be set to the location of the new version.

    ##  Callback for the message that is spawned when there is a new version.
    def actionTriggered(self, message, action):
        if action == "download":
            if self._download_url is not None:
                QDesktopServices.openUrl(QUrl(self._download_url))

    def run(self):
        self._download_url = None  # Reset download ur.
        if not self._url:
            Logger.log("e", "Can not check for a new release. URL not set!")
            return

        Logger.log("i", "Checking for new version of firmware")
        try:
            request = urllib.request.Request(self._url)
            current_version_file = urllib.request.urlopen(request)
            reader = codecs.getreader("utf-8")

            # Nothing to parse, just get the string
            # TODO: In the future may be done by parsing a JSON file
            current_version = reader(current_version_file).readline().rstrip()
            Logger.log("i", "Reading firmware version: %s" % current_version)

            # If it is the first time the version is checked, the checked_version is None
            checked_version = Preferences.getInstance().getValue("info/latest_checked_firmware")
            active_machine = Preferences.getInstance().getValue("cura/active_machine")
            # If it is not None, then we compare between the checked_version and the current_version
            # Now we just do that if the active printer is Ultimaker 3 or Ultimaker 3 Extended
            if ((active_machine == "Ultimaker 3 Extended") or (active_machine == "Ultimaker 3"))\
                    and ((checked_version is None) or (checked_version != current_version)):
                message = Message(i18n_catalog.i18nc("@info", "<b>New %s firmware available</b><br/><br/>To ensure that your "
                                                              "%s is equiped with the latest features it is recommended "
                                                              "to update the firmware regularly. This can be done on the "
                                                              "%s (when connected to the network) or via USB."
                                                     % (active_machine, active_machine, active_machine)))
                message.addAction("download", i18n_catalog.i18nc("@action:button", "Download"), "[no_icon]", "[no_description]")

                # If we do this in a cool way, the download url should be available in the JSON file
                self._download_url = "https://ultimaker.com/en/resources/20500-upgrade-firmware"
                message.actionTriggered.connect(self.actionTriggered)
                # Sometimes it's shown, sometimes not
                #message.show()
                Application.getInstance().showMessage(message)

                Preferences.getInstance().setValue("info/latest_checked_firmware", current_version)

        except Exception as e:
            Logger.log("w", "Failed to check for new version: %s" % e)
            if not self.silent:
                Message(i18n_catalog.i18nc("@info", "Could not access update information.")).show()
            return