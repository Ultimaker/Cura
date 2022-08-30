# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade50to52

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade50to52.VersionUpgrade50to52()

def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            ("machine_stack", 5000020): ("machine_stack", 6000020, upgrade.upgradeMachine),
            ("extruder_train", 5000020): ("extruder_train", 6000020, upgrade.upgradeStack),
        },
        "sources": {
            "extruder_train": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./extruders"}
            },
            "machine_stack": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./machine_instances"},
            },
        },
    }


def register(_app: "Application") -> Dict[str, Any]:
    return { "version_upgrade": upgrade }
