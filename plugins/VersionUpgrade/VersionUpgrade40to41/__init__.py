# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade40to41

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade40to41.VersionUpgrade40to41()

def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                           To                              Upgrade function
            ("preferences", 6000006):        ("preferences", 6000007, upgrade.upgradePreferences),
            ("machine_stack", 4000006):      ("machine_stack", 4000007,      upgrade.upgradeStack),
            ("extruder_train", 4000006):     ("extruder_train", 4000007,     upgrade.upgradeStack),
            ("definition_changes", 4000006): ("definition_changes", 4000007, upgrade.upgradeInstanceContainer),
            ("quality_changes", 4000006):    ("quality_changes", 4000007,    upgrade.upgradeInstanceContainer),
            ("quality", 4000006):            ("quality", 4000007,            upgrade.upgradeInstanceContainer),
            ("user", 4000006):               ("user", 4000007,               upgrade.upgradeInstanceContainer),
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
            "definition_changes": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./definition_changes"}
            },
            "quality_changes": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./quality_changes"}
            },
            "quality": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./quality"}
            },
            "user": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./user"}
            }
        }
    }


def register(app: "Application") -> Dict[str, Any]:
    return { "version_upgrade": upgrade }
