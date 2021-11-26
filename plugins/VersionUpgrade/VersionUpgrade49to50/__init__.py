# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade49to50

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade49to50.VersionUpgrade49to50()

def getMetaData() -> Dict[str, Any]:
    return {  # Since there is no VersionUpgrade from 48 to 49 yet, upgrade the 48 profiles to 50.
        "version_upgrade": {
            # From                           To                              Upgrade function
            ("preferences", 6000016):        ("preferences", 6000018,        upgrade.upgradePreferences),
            ("machine_stack", 5000016):      ("machine_stack", 5000018,      upgrade.upgradeStack),
            ("extruder_train", 5000016):     ("extruder_train", 5000018,     upgrade.upgradeStack),
            ("machine_stack", 4000018):      ("machine_stack", 5000018,      upgrade.upgradeStack),  # We made a mistake in the arachne beta 1
            ("extruder_train", 4000018):     ("extruder_train", 5000018,     upgrade.upgradeStack),  # We made a mistake in the arachne beta 1
            ("definition_changes", 4000016): ("definition_changes", 4000018, upgrade.upgradeInstanceContainer),
            ("quality_changes", 4000016):    ("quality_changes", 4000018,    upgrade.upgradeInstanceContainer),
            ("quality", 4000016):            ("quality", 4000018,            upgrade.upgradeInstanceContainer),
            ("user", 4000016):               ("user", 4000018,               upgrade.upgradeInstanceContainer),
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
