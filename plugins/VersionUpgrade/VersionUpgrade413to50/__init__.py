# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade413to50

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade413to50.VersionUpgrade413to50()

def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                           To                              Upgrade function
            ("preferences", 7000019):        ("preferences", 7000020,        upgrade.upgradePreferences),
            ("machine_stack", 5000019):      ("machine_stack", 5000020,      upgrade.upgradeStack),
            ("extruder_train", 5000019):     ("extruder_train", 5000020,     upgrade.upgradeStack),
            ("definition_changes", 4000019): ("definition_changes", 4000020, upgrade.upgradeInstanceContainer),
            ("quality_changes", 4000019):    ("quality_changes", 4000020,    upgrade.upgradeInstanceContainer),
            ("quality", 4000019):            ("quality", 4000020,            upgrade.upgradeInstanceContainer),
            ("user", 4000019):               ("user", 4000020,               upgrade.upgradeInstanceContainer),
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
