# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import List, Optional

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")


def getSettingsKeyForMachine(machine_id: int) -> str:
    return "info/latest_checked_firmware_for_{0}".format(machine_id)


class FirmwareUpdateCheckerLookup:

    def __init__(self, machine_name, machine_json) -> None:
        # Parse all the needed lookup-tables from the ".json" file(s) in the resources folder.
        self._machine_id = machine_json.get("id")
        self._machine_name = machine_name.lower()  # Lower in-case upper-case chars are added to the original json.
        self._check_urls = []  # type:List[str]
        for check_url in machine_json.get("check_urls", []):
            self._check_urls.append(check_url)
        self._redirect_user = machine_json.get("update_url")

    def getMachineId(self) -> Optional[int]:
        return self._machine_id

    def getMachineName(self) -> Optional[int]:
        return self._machine_name

    def getCheckUrls(self) -> Optional[List[str]]:
        return self._check_urls

    def getRedirectUserUrl(self) -> Optional[str]:
        return self._redirect_user
