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
            ("preferences", 6000016):        ("preferences", 7000016,        upgrade.upgradePreferences),
            ("machine_stack", 4000016):      ("machine_stack", 5000016,      upgrade.upgradeStack),
            ("extruder_train", 4000016):     ("extruder_train", 5000016,     upgrade.upgradeStack),
            ("setting_visibility", 1000000): ("setting_visibility", 2000016, upgrade.upgradeSettingVisibility),
        },
        "sources": {
            "preferences": {
                "get_version": upgrade.getCfgVersion,
                "location": {"."}
            },
            "machine_stack": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./machine_instances"}
            },
            "extruder_train": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./extruders"}
            },
            "setting_visibility": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./setting_visibility"}
            }
        }
    }


def register(app: "Application") -> Dict[str, Any]:
    return {"version_upgrade": upgrade}
