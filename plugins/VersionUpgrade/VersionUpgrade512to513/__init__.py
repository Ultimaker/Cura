# Copyright (c) 2026 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade512to513

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade512to513.VersionUpgrade512to513()

def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                           To                              Upgrade function
            ("preferences", 7000026):        ("preferences", 7000027,        upgrade.upgradePreferences),
            ("machine_stack", 6000026):      ("machine_stack", 6000027,      upgrade.upgradeStack),
            ("extruder_train", 6000026):     ("extruder_train", 6000027,     upgrade.upgradeStack),
            ("definition_changes", 4000026): ("definition_changes", 4000027, upgrade.upgradeInstanceContainer),
            ("quality_changes", 4000026):    ("quality_changes", 4000027,    upgrade.upgradeInstanceContainer),
            ("quality", 4000026):            ("quality", 4000027,            upgrade.upgradeInstanceContainer),
            ("user", 4000026):               ("user", 4000027,               upgrade.upgradeInstanceContainer),
            ("intent", 4000026):             ("intent", 4000027,             upgrade.upgradeInstanceContainer),
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
