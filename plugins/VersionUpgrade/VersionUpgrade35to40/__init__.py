from typing import Dict, Any

from . import VersionUpgrade35to40

upgrade = VersionUpgrade35to40.VersionUpgrade35to40()


def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                           To                              Upgrade function
            ("preferences", 6000005):        ("preferences", 6000006,        upgrade.upgradePreferences),

            ("definition_changes", 4000005): ("definition_changes", 4000006, upgrade.upgradeInstanceContainer),
            ("quality_changes", 4000005):    ("quality_changes", 4000006,    upgrade.upgradeInstanceContainer),
            ("quality", 4000005):            ("quality", 4000006,            upgrade.upgradeInstanceContainer),
            ("user", 4000005):               ("user", 4000006,               upgrade.upgradeInstanceContainer),

            ("machine_stack", 4000005):      ("machine_stack", 4000006,      upgrade.upgradeStack),
            ("extruder_train", 4000005):     ("extruder_train", 4000006,     upgrade.upgradeStack),
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


def register(app) -> Dict[str, Any]:
    return {"version_upgrade": upgrade}