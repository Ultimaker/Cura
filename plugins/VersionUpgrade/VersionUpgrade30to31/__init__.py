# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade30to31

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade30to31.VersionUpgrade30to31()

def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                    To                       Upgrade function
            ("preferences", 5000003): ("preferences", 5000004, upgrade.upgradePreferences),

            ("machine_stack", 3000003):     ("machine_stack", 3000004,     upgrade.upgradeStack),
            ("extruder_train", 3000003):    ("extruder_train", 3000004,    upgrade.upgradeStack),

            ("quality_changes", 2000003):    ("quality_changes", 2000004,    upgrade.upgradeInstanceContainer),
            ("user", 2000003):               ("user", 2000004,               upgrade.upgradeInstanceContainer),
            ("definition_changes", 2000003): ("definition_changes", 2000004, upgrade.upgradeInstanceContainer),
            ("variant", 2000003):            ("variant", 2000004,            upgrade.upgradeInstanceContainer)
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
            "quality": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./quality"}
            },
            "quality_changes": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./quality"}
            },
            "user": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./user"}
            },
            "definition_changes": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./definition_changes"}
            },
            "variant": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./variants"}
            }
        }
    }

def register(app: "Application") -> Dict[str, Any]:
    return { "version_upgrade": upgrade }
