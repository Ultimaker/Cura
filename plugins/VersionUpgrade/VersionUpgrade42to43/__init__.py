# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade42to43

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade42to43.VersionUpgrade42to43()

def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                           To                              Upgrade function
            ("machine_stack", 4000008):      ("machine_stack", 4000009,      upgrade.upgradeStack),
            ("extruder_train", 4000008):     ("extruder_train", 4000009,     upgrade.upgradeStack),
            ("definition_changes", 4000008): ("definition_changes", 4000009, upgrade.upgradeInstanceContainer),
            ("quality_changes", 4000008):    ("quality_changes", 4000009,    upgrade.upgradeInstanceContainer),
            ("quality", 4000008):            ("quality", 4000009,            upgrade.upgradeInstanceContainer),
            ("user", 4000008):               ("user", 4000009,               upgrade.upgradeInstanceContainer),
        },
        "sources": {
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