# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from enum import Enum, unique

from UM.Application import Application
from UM.Message import Message
from UM.Logger import Logger
from UM.Job import Job
from UM.Version import Version

import urllib.request
from urllib.error import URLError
import codecs

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")

# For UM-machines, these need to match the unique firmware-ID (also used in the URLs), i.o.t. only define in one place.
@unique
class MachineId(Enum):
    UM3 = 9066
    UM3E = 9511
    S5 = 9051


def get_settings_key_for_machine(machine_id: MachineId) -> str:
    return "info/latest_checked_firmware_for_{0}".format(machine_id.value)


def default_parse_version_response(response: str) -> Version:
    raw_str = response.split('\n', 1)[0].rstrip()
    return Version(raw_str.split('.'))  # Split it into a list; the default parsing of 'single string' is different.


##  This job checks if there is an update available on the provided URL.
class FirmwareUpdateCheckerJob(Job):
    MACHINE_PER_NAME = \
        {
            "ultimaker 3": MachineId.UM3,
            "ultimaker 3 extended": MachineId.UM3E,
            "ultimaker s5": MachineId.S5
        }
    PARSE_VERSION_URL_PER_MACHINE = \
        {
            MachineId.UM3: default_parse_version_response,
            MachineId.UM3E: default_parse_version_response,
            MachineId.S5: default_parse_version_response
        }
    REDIRECT_USER_PER_MACHINE = \
        {
            MachineId.UM3: "https://ultimaker.com/en/resources/20500-upgrade-firmware",
            MachineId.UM3E: "https://ultimaker.com/en/resources/20500-upgrade-firmware",
            MachineId.S5: "https://ultimaker.com/en/resources/20500-upgrade-firmware"
        }
    # TODO: Parse all of that from a file, because this will be a big mess of large static values which gets worse with each printer.

    def __init__(self, container=None, silent=False, urls=None, callback=None, set_download_url_callback=None):
        super().__init__()
        self._container = container
        self.silent = silent
        self._urls = urls
        self._callback = callback
        self._set_download_url_callback = set_download_url_callback

        self._headers = {}  # Don't set headers yet.

    def getUrlResponse(self, url: str) -> str:
        result = "0.0.0"

        try:
            request = urllib.request.Request(url, headers=self._headers)
            current_version_file = urllib.request.urlopen(request)
            reader = codecs.getreader("utf-8")
            result = reader(current_version_file).read(firstline=True)
        except URLError:
            Logger.log('w', "Could not reach '{0}', if this URL is old, consider removal.".format(url))

        return result

    def getCurrentVersionForMachine(self, machine_id: MachineId) -> Version:
        max_version = Version([0, 0, 0])

        machine_urls = self._urls.get(machine_id)
        parse_function = self.PARSE_VERSION_URL_PER_MACHINE.get(machine_id)
        if machine_urls is not None and parse_function is not None:
            for url in machine_urls:
                version = parse_function(self.getUrlResponse(url))
                if version > max_version:
                    max_version = version

        if max_version < Version([0, 0, 1]):
            Logger.log('w', "MachineID {0} not handled!".format(repr(machine_id)))

        return max_version

    def run(self):
        if not self._urls or self._urls is None:
            Logger.log("e", "Can not check for a new release. URL not set!")
            return

        try:
            application_name = Application.getInstance().getApplicationName()
            application_version = Application.getInstance().getVersion()
            self._headers = {"User-Agent": "%s - %s" % (application_name, application_version)}

            # get machine name from the definition container
            machine_name = self._container.definition.getName()
            machine_name_parts = machine_name.lower().split(" ")

            # If it is not None, then we compare between the checked_version and the current_version
            machine_id = self.MACHINE_PER_NAME.get(machine_name.lower())
            if machine_id is not None:
                Logger.log("i", "You have a {0} in the printer list. Let's check the firmware!".format(machine_name))

                current_version = self.getCurrentVersionForMachine(machine_id)

                # If it is the first time the version is checked, the checked_version is ''
                setting_key_str = get_settings_key_for_machine(machine_id)
                checked_version = Application.getInstance().getPreferences().getValue(setting_key_str)

                # If the checked_version is '', it's because is the first time we check firmware and in this case
                # we will not show the notification, but we will store it for the next time
                Application.getInstance().getPreferences().setValue(setting_key_str, current_version)
                Logger.log("i", "Reading firmware version of %s: checked = %s - latest = %s", machine_name, checked_version, current_version)

                # The first time we want to store the current version, the notification will not be shown,
                # because the new version of Cura will be release before the firmware and we don't want to
                # notify the user when no new firmware version is available.
                if (checked_version != "") and (checked_version != current_version):
                    Logger.log("i", "SHOWING FIRMWARE UPDATE MESSAGE")

                    message = Message(i18n_catalog.i18nc(
                        "@info Don't translate {machine_name}, since it gets replaced by a printer name!",
                        "New features are available for your {machine_name}! It is recommended to update the firmware on your printer.").format(
                        machine_name=machine_name),
                        title=i18n_catalog.i18nc(
                                          "@info:title The %s gets replaced with the printer name.",
                                          "New %s firmware available") % machine_name)

                    message.addAction("download",
                                      i18n_catalog.i18nc("@action:button", "How to update"),
                                      "[no_icon]",
                                      "[no_description]",
                                      button_style=Message.ActionButtonStyle.LINK,
                                      button_align=Message.ActionButtonStyle.BUTTON_ALIGN_LEFT)

                    # If we do this in a cool way, the download url should be available in the JSON file
                    if self._set_download_url_callback:
                        redirect = self.REDIRECT_USER_PER_MACHINE.get(machine_id)
                        if redirect is not None:
                            self._set_download_url_callback(redirect)
                        else:
                            Logger.log('w', "No callback-url for firmware of {0}".format(repr(machine_id)))
                    message.actionTriggered.connect(self._callback)
                    message.show()
            else:
                Logger.log('i', "No machine with name {0} in list of firmware to check.".format(repr(machine_id)))

        except Exception as e:
            Logger.log("w", "Failed to check for new version: %s", e)
            if not self.silent:
                Message(i18n_catalog.i18nc("@info", "Could not access update information.")).show()
            return
