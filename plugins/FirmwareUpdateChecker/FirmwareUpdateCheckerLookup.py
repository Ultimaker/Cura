# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import json

from typing import Callable, Dict, List, Optional

from UM.Logger import Logger
from UM.Version import Version

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")


def get_settings_key_for_machine(machine_id: int) -> str:
    return "info/latest_checked_firmware_for_{0}".format(machine_id)


def default_parse_version_response(response: str) -> Version:
    raw_str = response.split("\n", 1)[0].rstrip()
    return Version(raw_str.split("."))  # Split it into a list; the default parsing of "single string" is different.


class FirmwareUpdateCheckerLookup:
    JSON_NAME_TO_VERSION_PARSE_FUNCTION = {"default": default_parse_version_response}

    def __init__(self, json_path) -> None:
        # Open the .json file with the needed lookup-lists for each machine(/model) and retrieve "raw" json.
        with open(json_path, "r", encoding = "utf-8") as json_file:
            machines_json = json.load(json_file).get("machines")
        if machines_json is None:
            Logger.log("e", "Missing or inaccessible: {0}".format(json_path))
            return

        # Parse all the needed lookup-tables from the ".json" file(s) in the resources folder.
        self._machine_ids = []  # type:List[int]
        self._machine_per_name = {}  # type:Dict[str, int]
        self._parse_version_url_per_machine = {}  # type:Dict[int, Callable]
        self._check_urls_per_machine = {}  # type:Dict[int, List[str]]
        self._redirect_user_per_machine = {}  # type:Dict[int, str]
        try:
            for machine_json in machines_json:
                machine_id = machine_json.get("id")
                machine_name = machine_json.get("name").lower()  # Lower in case upper-case char are added to the json.
                self._machine_ids.append(machine_id)
                self._machine_per_name[machine_name] = machine_id
                version_parse_function = \
                    self.JSON_NAME_TO_VERSION_PARSE_FUNCTION.get(machine_json.get("version_parser"))
                if version_parse_function is None:
                    Logger.log("w", "No version-parse-function specified for machine {0}.".format(machine_name))
                    version_parse_function = default_parse_version_response  # Use default instead if nothing is found.
                self._parse_version_url_per_machine[machine_id] = version_parse_function
                self._check_urls_per_machine[machine_id] = []  # Multiple check-urls: see "_comment" in the .json file.
                for check_url in machine_json.get("check_urls"):
                    self._check_urls_per_machine[machine_id].append(check_url)
                self._redirect_user_per_machine[machine_id] = machine_json.get("update_url")
        except Exception as ex:
            Logger.log("e", "Couldn't parse firmware-update-check lookup-lists from file because {0}.".format(ex))

    def getMachineIds(self) -> List[int]:
        return self._machine_ids

    def getMachineByName(self, machine_name: str) -> Optional[int]:
        return self._machine_per_name.get(machine_name)

    def getParseVersionUrlFor(self, machine_id: int) -> Optional[Callable]:
        return self._parse_version_url_per_machine.get(machine_id)

    def getCheckUrlsFor(self, machine_id: int) -> Optional[List[str]]:
        return self._check_urls_per_machine.get(machine_id)

    def getRedirectUserFor(self, machine_id: int) -> Optional[str]:
        return self._redirect_user_per_machine.get(machine_id)
