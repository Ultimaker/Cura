# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade41to42

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade41to42.VersionUpgrade41to42()

def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                           To                              Upgrade function
            ("machine_stack", 4000007):      ("machine_stack", 5000007,      upgrade.upgradeStack),
            ("extruder_train", 4000007):     ("extruder_train", 5000007,     upgrade.upgradeStack)
        },
        "sources": {
            "machine_stack": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./machine_instances"}
            },
            "extruder_train": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./extruders"}
            }
        }
    }


def register(app: "Application") -> Dict[str, Any]:
    return {"version_upgrade": upgrade}
