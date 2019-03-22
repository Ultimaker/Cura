# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade32to33

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade32to33.VersionUpgrade32to33()

def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                           To                              Upgrade function
            ("preferences", 5000004):        ("preferences", 6000004,        upgrade.upgradePreferences),

            ("machine_stack", 3000004):      ("machine_stack", 4000004,      upgrade.upgradeStack),
            ("extruder_train", 3000004):     ("extruder_train", 4000004,     upgrade.upgradeStack),

            ("definition_changes", 2000004): ("definition_changes", 3000004, upgrade.upgradeInstanceContainer),
            ("quality_changes", 2000004):    ("quality_changes", 3000004,    upgrade.upgradeQualityChanges),
            ("user", 2000004):               ("user", 3000004,               upgrade.upgradeInstanceContainer),
            ("variant", 2000004):            ("variant", 3000004,            upgrade.upgradeVariants)
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
                "location": {"./quality"}
            },
            "user": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./user", "./materials/*"}
            },
            "variant": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./variants"}
            }
        }
    }

def register(app: "Application") -> Dict[str, Any]:
    return { "version_upgrade": upgrade }