# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade460to462

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade460to462.VersionUpgrade460to462()

def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                           To                              Upgrade function
            ("preferences", 6000012):        ("preferences", 6000013,        upgrade.upgradePreferences),
            ("machine_stack", 4000012):      ("machine_stack", 4000013,      upgrade.upgradeStack),
            ("extruder_train", 4000012):     ("extruder_train", 4000013,     upgrade.upgradeStack),
            ("definition_changes", 4000012): ("definition_changes", 4000013, upgrade.upgradeInstanceContainer),
            ("quality_changes", 4000012):    ("quality_changes", 4000013,    upgrade.upgradeInstanceContainer),
            ("quality", 4000012):            ("quality", 4000013,            upgrade.upgradeInstanceContainer),
            ("user", 4000012):               ("user", 4000013,               upgrade.upgradeInstanceContainer),
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
