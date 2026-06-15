# Copyright (c) 2026 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade511to512

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade511to512.VersionUpgrade511to512()

def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                           To                              Upgrade function
            ("preferences", 7000025):        ("preferences", 7000026,        upgrade.upgradePreferences),
            ("machine_stack", 6000025):      ("machine_stack", 6000026,      upgrade.upgradeStack),
            ("extruder_train", 6000025):     ("extruder_train", 6000026,     upgrade.upgradeStack),
            ("definition_changes", 4000025): ("definition_changes", 4000026, upgrade.upgradeInstanceContainer),
            ("quality_changes", 4000025):    ("quality_changes", 4000026,    upgrade.upgradeInstanceContainer),
            ("quality", 4000025):            ("quality", 4000026,            upgrade.upgradeInstanceContainer),
            ("user", 4000025):               ("user", 4000026,               upgrade.upgradeInstanceContainer),
            ("intent", 4000025):             ("intent", 4000026,             upgrade.upgradeInstanceContainer),
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
