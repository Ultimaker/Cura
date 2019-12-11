# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade25to26

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade25to26.VersionUpgrade25to26()

def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                          To                          Upgrade function
            ("preferences", 4000000):     ("preferences", 4000001,     upgrade.upgradePreferences),
            # NOTE: All the instance containers share the same general/version, so we have to update all of them
            #       if any is updated.
            ("quality_changes", 2000000):       ("quality_changes", 2000001,    upgrade.upgradeInstanceContainer),
            ("user", 2000000):                  ("user", 2000001,               upgrade.upgradeInstanceContainer),
            ("definition_changes", 2000000):    ("definition_changes", 2000001, upgrade.upgradeInstanceContainer),
            ("machine_stack", 3000000):         ("machine_stack", 3000001,      upgrade.upgradeMachineStack),
        },
        "sources": {
            "quality_changes": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./quality"}
            },
            "preferences": {
                "get_version": upgrade.getCfgVersion,
                "location": {"."}
            },
            "user": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./user"}
            },
            "definition_changes": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./machine_instances"}
            },
            "machine_stack": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./machine_instances"}
            }
        }
    }

def register(app: "Application") -> Dict[str, Any]:
    return { "version_upgrade": upgrade }
