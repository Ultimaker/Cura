# Copyright (c) 2024 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade59to510

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade59to510.VersionUpgrade59to510()

def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                           To                              Upgrade function
            ("preferences", 7000024):        ("preferences", 7000025,        upgrade.upgradePreferences),
            ("machine_stack", 6000024):      ("machine_stack", 6000025,      upgrade.upgradeStack),
            ("extruder_train", 6000024):     ("extruder_train", 6000025,     upgrade.upgradeStack),
            ("definition_changes", 4000024): ("definition_changes", 4000025, upgrade.upgradeInstanceContainer),
            ("quality_changes", 4000024):    ("quality_changes", 4000025,    upgrade.upgradeInstanceContainer),
            ("quality", 4000024):            ("quality", 4000025,            upgrade.upgradeInstanceContainer),
            ("user", 4000024):               ("user", 4000025,               upgrade.upgradeInstanceContainer),
            ("intent", 4000024):             ("intent", 4000025,             upgrade.upgradeInstanceContainer),
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
