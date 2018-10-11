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


def get_settings_key_for_machine(machine_id: int) -> str:
    return "info/latest_checked_firmware_for_{0}".format(machine_id)


def default_parse_version_response(response: str) -> Version:
    raw_str = response.split('\n', 1)[0].rstrip()
    return Version(raw_str.split('.'))  # Split it into a list; the default parsing of 'single string' is different.


##  This job checks if there is an update available on the provided URL.
class FirmwareUpdateCheckerJob(Job):
    STRING_ZERO_VERSION = "0.0.0"
    STRING_EPSILON_VERSION = "0.0.1"
    ZERO_VERSION = Version(STRING_ZERO_VERSION)
    EPSILON_VERSION = Version(STRING_EPSILON_VERSION)
    JSON_NAME_TO_VERSION_PARSE_FUNCTION = {"default": default_parse_version_response}

    def __init__(self, container=None, silent=False, machines_json=None, callback=None, set_download_url_callback=None):
        super().__init__()
        self._container = container
        self.silent = silent

        # Parse all the needed lookup-tables from the '.json' file(s) in the resources folder.
        # TODO: This should not be here when the merge to master is done, as it will be repeatedly recreated.
        #       It should be a separate object this constructor receives instead.
        self._machine_ids = []
        self._machine_per_name = {}
        self._parse_version_url_per_machine = {}
        self._check_urls_per_machine = {}
        self._redirect_user_per_machine = {}
        try:
            for machine_json in machines_json:
                machine_id = machine_json.get("id")
                machine_name = machine_json.get("name")
                self._machine_ids.append(machine_id)
                self._machine_per_name[machine_name] = machine_id
                version_parse_function = self.JSON_NAME_TO_VERSION_PARSE_FUNCTION.get(machine_json.get("version_parser"))
                if version_parse_function is None:
                    Logger.log('w', "No version-parse-function specified for machine {0}.".format(machine_name))
                    version_parse_function = default_parse_version_response  # Use default instead if nothing is found.
                self._parse_version_url_per_machine[machine_id] = version_parse_function
                self._check_urls_per_machine[machine_id] = []  # Multiple check-urls: see '_comment' in the .json file.
                for check_url in machine_json.get("check_urls"):
                    self._check_urls_per_machine[machine_id].append(check_url)
                self._redirect_user_per_machine[machine_id] = machine_json.get("update_url")
        except:
            Logger.log('e', "Couldn't parse firmware-update-check loopup-lists from file.")

        self._callback = callback
        self._set_download_url_callback = set_download_url_callback

        self._headers = {}  # Don't set headers yet.

    def getUrlResponse(self, url: str) -> str:
        result = self.STRING_ZERO_VERSION

        try:
            request = urllib.request.Request(url, headers=self._headers)
            current_version_file = urllib.request.urlopen(request)
            reader = codecs.getreader("utf-8")
            result = reader(current_version_file).read(firstline=True)
        except URLError:
            Logger.log('w', "Could not reach '{0}', if this URL is old, consider removal.".format(url))

        return result

    def getCurrentVersionForMachine(self, machine_id: int) -> Version:
        max_version = self.ZERO_VERSION

        machine_urls = self._check_urls_per_machine.get(machine_id)
        parse_function = self._parse_version_url_per_machine.get(machine_id)
        if machine_urls is not None and parse_function is not None:
            for url in machine_urls:
                version = parse_function(self.getUrlResponse(url))
                if version > max_version:
                    max_version = version

        if max_version < self.EPSILON_VERSION:
            Logger.log('w', "MachineID {0} not handled!".format(repr(machine_id)))

        return max_version

    def run(self):
        if not self._machine_ids or self._machine_ids is None:
            Logger.log("e", "Can not check for a new release. URL not set!")
            return

        try:
            application_name = Application.getInstance().getApplicationName()
            application_version = Application.getInstance().getVersion()
            self._headers = {"User-Agent": "%s - %s" % (application_name, application_version)}

            # get machine name from the definition container
            machine_name = self._container.definition.getName()

            # If it is not None, then we compare between the checked_version and the current_version
            machine_id = self._machine_per_name.get(machine_name.lower())
            if machine_id is not None:
                Logger.log("i", "You have a {0} in the printer list. Let's check the firmware!".format(machine_name))

                current_version = self.getCurrentVersionForMachine(machine_id)

                # If it is the first time the version is checked, the checked_version is ''
                setting_key_str = get_settings_key_for_machine(machine_id)
                checked_version = Version(Application.getInstance().getPreferences().getValue(setting_key_str))

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
                        redirect = self._redirect_user_per_machine.get(machine_id)
                        if redirect is not None:
                            self._set_download_url_callback(redirect)
                        else:
                            Logger.log('w', "No callback-url for firmware of {0}".format(repr(machine_id)))
                    message.actionTriggered.connect(self._callback)
                    message.show()
            else:
                Logger.log('i', "No machine with name {0} in list of firmware to check.".format(machine_name))

        except Exception as e:
            Logger.log("w", "Failed to check for new version: %s", e)
            if not self.silent:
                Message(i18n_catalog.i18nc("@info", "Could not access update information.")).show()
            return
