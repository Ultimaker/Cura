# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade33to34

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade33to34.VersionUpgrade33to34()

def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                           To                              Upgrade function
            ("definition_changes", 3000004): ("definition_changes", 4000004, upgrade.upgradeInstanceContainer),
            ("quality_changes", 3000004):    ("quality_changes", 4000004,    upgrade.upgradeInstanceContainer),
            ("quality", 3000004):            ("quality", 4000004,            upgrade.upgradeInstanceContainer),
            ("user", 3000004):               ("user", 4000004,               upgrade.upgradeInstanceContainer),
        },
        "sources": {
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
    return { "version_upgrade": upgrade }
