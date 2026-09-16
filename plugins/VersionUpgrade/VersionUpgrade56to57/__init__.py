# Copyright (c) 2024 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade56to57

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade56to57.VersionUpgrade56to57()


def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                           To                              Upgrade function
            ("preferences", 7000022):        ("preferences", 7000023,        upgrade.upgradePreferences),
            ("machine_stack", 6000022):      ("machine_stack", 6000023,      upgrade.upgradeStack),
            ("extruder_train", 6000022):     ("extruder_train", 6000023,     upgrade.upgradeStack),
            ("definition_changes", 4000022): ("definition_changes", 4000023, upgrade.upgradeInstanceContainer),
            ("quality_changes", 4000022):    ("quality_changes", 4000023,    upgrade.upgradeInstanceContainer),
            ("quality", 4000022):            ("quality", 4000023,            upgrade.upgradeInstanceContainer),
            ("user", 4000022):               ("user", 4000023,               upgrade.upgradeInstanceContainer),
            ("intent", 4000022):             ("intent", 4000023,             upgrade.upgradeInstanceContainer),
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
