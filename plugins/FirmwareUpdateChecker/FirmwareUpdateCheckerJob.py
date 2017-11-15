# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Preferences import Preferences
from UM.Application import Application
from UM.Message import Message
from UM.Logger import Logger
from UM.Job import Job

import urllib.request
import codecs

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")


##  This job checks if there is an update available on the provided URL.
class FirmwareUpdateCheckerJob(Job):
    def __init__(self, container = None, silent = False, url = None, callback = None, set_download_url_callback = None):
        super().__init__()
        self._container = container
        self.silent = silent
        self._url = url
        self._callback = callback
        self._set_download_url_callback = set_download_url_callback

    def run(self):
        if not self._url:
            Logger.log("e", "Can not check for a new release. URL not set!")
            return

        try:
            application_name = Application.getInstance().getApplicationName()
            headers = {"User-Agent": "%s - %s" % (application_name, Application.getInstance().getVersion())}
            request = urllib.request.Request(self._url, headers = headers)
            current_version_file = urllib.request.urlopen(request)
            reader = codecs.getreader("utf-8")

            # get machine name from the definition container
            machine_name = self._container.definition.getName()
            machine_name_parts = machine_name.lower().split(" ")

            # If it is not None, then we compare between the checked_version and the current_version
            # Now we just do that if the active printer is Ultimaker 3 or Ultimaker 3 Extended or any
            # other Ultimaker 3 that will come in the future
            if len(machine_name_parts) >= 2 and machine_name_parts[:2] == ["ultimaker", "3"]:
                # Nothing to parse, just get the string
                # TODO: In the future may be done by parsing a JSON file with diferent version for each printer model
                current_version = reader(current_version_file).readline().rstrip()

                # If it is the first time the version is checked, the checked_version is ''
                checked_version = Preferences.getInstance().getValue("info/latest_checked_firmware")

                # If the checked_version is '', it's because is the first time we check firmware and in this case
                # we will not show the notification, but we will store it for the next time
                Preferences.getInstance().setValue("info/latest_checked_firmware", current_version)
                Logger.log("i", "Reading firmware version of %s: checked = %s - latest = %s", machine_name, checked_version, current_version)

                # The first time we want to store the current version, the notification will not be shown,
                # because the new version of Cura will be release before the firmware and we don't want to
                # notify the user when no new firmware version is available.
                if (checked_version != "") and (checked_version != current_version):
                    Logger.log("i", "SHOWING FIRMWARE UPDATE MESSAGE")
                    message = Message(i18n_catalog.i18nc("@info Don't translate {machine_name}, since it gets replaced by a printer name!", "New features are available for your {machine_name}! It is recommended to update the firmware on your printer.").format(machine_name = machine_name),
                                      title = i18n_catalog.i18nc("@info:title The %s gets replaced with the printer name.", "New %s firmware available") % machine_name)
                    message.addAction("download", i18n_catalog.i18nc("@action:button", "How to update"), "[no_icon]", "[no_description]")

                    # If we do this in a cool way, the download url should be available in the JSON file
                    if self._set_download_url_callback:
                        self._set_download_url_callback("https://ultimaker.com/en/resources/20500-upgrade-firmware")
                    message.actionTriggered.connect(self._callback)
                    message.show()

        except Exception as e:
            Logger.log("w", "Failed to check for new version: %s", e)
            if not self.silent:
                Message(i18n_catalog.i18nc("@info", "Could not access update information.")).show()
            return
