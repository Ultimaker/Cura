# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade21to22

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade21to22.VersionUpgrade21to22()

def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                         To                         Upgrade function
            ("profile", 1000000):          ("quality", 2000000,       upgrade.upgradeProfile),
            ("machine_instance", 1000000): ("machine_stack", 2000000, upgrade.upgradeMachineInstance),
            ("preferences", 2000000):      ("preferences", 3000000,   upgrade.upgradePreferences)
        },
        "sources": {
            "profile": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./profiles", "./instance_profiles"}
            },
            "machine_instance": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./machine_instances"}
            },
            "preferences": {
                "get_version": upgrade.getCfgVersion,
                "location": {"."}
            },
            "user": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./user"}
            }
        }
    }

def register(app: "Application") -> Dict[str, Any]:
    return { "version_upgrade": upgrade }
