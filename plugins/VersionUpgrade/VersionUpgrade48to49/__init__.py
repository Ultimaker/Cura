# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade48to49

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade48to49.VersionUpgrade48to49()

def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                           To                              Upgrade function
            ("preferences", 6000016):        ("preferences", 6000017,        upgrade.upgradePreferences),
            ("setting_visibility", 1000000): ("setting_visibility", 2000017, upgrade.upgradeSettingVisibility),
        },
        "sources": {
            "preferences": {
                "get_version": upgrade.getCfgVersion,
                "location": {"."}
            },
            "setting_visibility": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./setting_visibility"}
            }
        }
    }


def register(app: "Application") -> Dict[str, Any]:
    return {"version_upgrade": upgrade}
