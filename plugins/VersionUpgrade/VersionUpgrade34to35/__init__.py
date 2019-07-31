# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade34to35

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade34to35.VersionUpgrade34to35()

def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                           To                              Upgrade function
            ("preferences", 6000004):        ("preferences", 6000005,        upgrade.upgradePreferences),

            ("definition_changes", 4000004): ("definition_changes", 4000005, upgrade.upgradeInstanceContainer),
            ("quality_changes", 4000004):    ("quality_changes", 4000005,    upgrade.upgradeInstanceContainer),
            ("quality", 4000004):            ("quality", 4000005,            upgrade.upgradeInstanceContainer),
            ("user", 4000004):               ("user", 4000005,               upgrade.upgradeInstanceContainer),

            ("machine_stack", 4000004):      ("machine_stack", 4000005,      upgrade.upgradeStack),
            ("extruder_train", 4000004):     ("extruder_train", 4000005,     upgrade.upgradeStack),
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
