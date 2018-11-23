# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade.VersionUpgrade22to24()

def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                         To                 Upgrade function
            ("machine_instance", 2000000): ("machine_stack",  3000000, upgrade.upgradeMachineInstance),
            ("extruder_train", 2000000):   ("extruder_train", 3000000, upgrade.upgradeExtruderTrain),
            ("preferences", 3000000):      ("preferences",    4000000, upgrade.upgradePreferences),
            ("quality", 2000000):          ("quality_changes", 2000000, upgrade.upgradeQuality),
        },
        "sources": {
            "machine_stack": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./machine_instances"}
            },
            "extruder_train": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./extruders"}
            },
        }
    }

def register(app: "Application"):
    return { "version_upgrade": upgrade }
