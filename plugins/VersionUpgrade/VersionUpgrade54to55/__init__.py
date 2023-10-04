# Copyright (c) 2023 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade54to55

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade54to55.VersionUpgrade54to55()


def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                           To                              Upgrade function
            ("machine_stack", 5000022):      ("machine_stack", 6000022,      upgrade.upgradeStack),
            ("extruder_train", 5000022):     ("extruder_train", 6000022,     upgrade.upgradeStack),
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
