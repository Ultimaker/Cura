# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade45to46


if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade45to46.VersionUpgrade44to45()


def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                           To                              Upgrade function
            ("preferences", 6000011): ("preferences", 6000012, upgrade.upgradePreferences),
            ("machine_stack", 4000011): ("machine_stack", 4000012, upgrade.upgradeStack),
            ("extruder_train", 4000011): ("extruder_train", 4000012, upgrade.upgradeStack),
            ("definition_changes", 4000011): ("definition_changes", 4000012, upgrade.upgradeInstanceContainer),
            ("quality_changes", 4000011): ("quality_changes", 4000012, upgrade.upgradeInstanceContainer),
            ("quality", 4000011): ("quality", 4000012, upgrade.upgradeInstanceContainer),
            ("user", 4000011): ("user", 4000012, upgrade.upgradeInstanceContainer),
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
