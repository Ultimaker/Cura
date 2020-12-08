# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade462to47

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade462to47.VersionUpgrade462to47()

def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                           To                              Upgrade function
            ("preferences", 6000014):        ("preferences", 6000015,        upgrade.upgradePreferences),
            ("machine_stack", 4000014):      ("machine_stack", 4000015,      upgrade.upgradeStack),
            ("extruder_train", 4000014):     ("extruder_train", 4000015,     upgrade.upgradeStack),
            ("definition_changes", 4000014): ("definition_changes", 4000015, upgrade.upgradeInstanceContainer),
            ("quality_changes", 4000014):    ("quality_changes", 4000015,    upgrade.upgradeInstanceContainer),
            ("quality", 4000014):            ("quality", 4000015,            upgrade.upgradeInstanceContainer),
            ("user", 4000014):               ("user", 4000015,               upgrade.upgradeInstanceContainer),
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
    return {"version_upgrade": upgrade}
