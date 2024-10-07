# Copyright (c) 2024 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade58to59

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade58to59.VersionUpgrade58to59()


def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                           To                              Upgrade function
            ("preferences", 7000023):        ("preferences", 7000024,        upgrade.upgradePreferences),
            ("machine_stack", 6000023):      ("machine_stack", 6000024,      upgrade.upgradeStack),
            ("extruder_train", 6000023):     ("extruder_train", 6000024,     upgrade.upgradeStack),
            ("definition_changes", 4000023): ("definition_changes", 4000024, upgrade.upgradeInstanceContainer),
            ("quality_changes", 4000023):    ("quality_changes", 4000024,    upgrade.upgradeInstanceContainer),
            ("quality", 4000023):            ("quality", 4000024,            upgrade.upgradeInstanceContainer),
            ("user", 4000023):               ("user", 4000024,               upgrade.upgradeInstanceContainer),
            ("intent", 4000023):             ("intent", 4000024,             upgrade.upgradeInstanceContainer),
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
