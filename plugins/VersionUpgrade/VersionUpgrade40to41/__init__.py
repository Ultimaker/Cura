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
            ("machine_stack", 4000005):      ("machine_stack", 4000006,      upgrade.upgradeStack),
            ("extruder_train", 4000005):     ("extruder_train", 4000006,     upgrade.upgradeStack),
            ("preferences", 6000005):        ("preferences", 6000006,        upgrade.upgradePreferences),
            ("definition_changes", 4000005): ("definition_changes", 4000006, upgrade.upgradeInstanceContainer),
            ("quality_changes", 4000005):    ("quality_changes", 4000006,    upgrade.upgradeInstanceContainer),
            ("quality", 4000005):            ("quality", 4000006,            upgrade.upgradeInstanceContainer),
            ("user", 4000005):               ("user", 4000006,               upgrade.upgradeInstanceContainer),
        },
        "sources": {
            "machine_stack": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./machine_instances"}
            },
            "extruder_train": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./extruders"}
            }
        }
    }


def register(app: "Application") -> Dict[str, Any]:
    return { "version_upgrade": upgrade }
