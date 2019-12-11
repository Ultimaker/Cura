# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade26to27

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade26to27.VersionUpgrade26to27()

def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                          To                             Upgrade function
            ("machine_stack", 3000001):     ("machine_stack", 3000002,     upgrade.upgradeStack),
            ("extruder_train", 3000000):    ("extruder_train", 3000002,    upgrade.upgradeStack),

            # In 2.6.x, Preferences are saved with "version = 4" and no setting_version.
            # This means those Preferences files will still be treated as "4.0" as defined in VersionUpgrade25to26,
            # so the 25to26 upgrade routine will be called again.
            #
            # To fix this, we first fix the upgrade routine for 25to26 so it actually upgrades to "4.1", and then
            # here we can upgrade from "4.1" to "4.2" safely.
            #
            ("preferences", 4000001):       ("preferences", 4000002,         upgrade.upgradePreferences),
            # NOTE: All the instance containers share the same general/version, so we have to update all of them
            #       if any is updated.
            ("quality_changes", 2000001):       ("quality_changes", 2000002,    upgrade.upgradeOtherContainer),
            ("user", 2000001):                  ("user", 2000002,               upgrade.upgradeOtherContainer),
            ("definition_changes", 2000001):    ("definition_changes", 2000002, upgrade.upgradeOtherContainer),
            ("variant", 2000000):               ("variant", 2000002,            upgrade.upgradeOtherContainer)
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
            "preferences": {
                "get_version": upgrade.getCfgVersion,
                "location": {"."}
            },
            "quality_changes": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./quality"}
            },
            "user": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./user"}
            },
            "definition_changes": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./definition_changes"}
            },
            "variant": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./variants"}
            }
        }
    }

def register(app: "Application") -> Dict[str, Any]:
    return { "version_upgrade": upgrade }
