# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade41to42

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade41to42.VersionUpgrade41to42()

def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                           To                              Upgrade function
            ("preferences", 6000007):        ("preferences", 6000008,        upgrade.upgradePreferences),
            ("machine_stack", 4000007):      ("machine_stack", 4000008,      upgrade.upgradeStack),
            ("extruder_train", 4000007):     ("extruder_train", 4000008,     upgrade.upgradeStack),
            ("definition_changes", 4000007): ("definition_changes", 4000008, upgrade.upgradeInstanceContainer),
            ("quality_changes", 4000007):    ("quality_changes", 4000008,    upgrade.upgradeInstanceContainer),
            ("quality", 4000007):            ("quality", 4000008,            upgrade.upgradeInstanceContainer),
            ("user", 4000007):               ("user", 4000008,               upgrade.upgradeInstanceContainer),
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