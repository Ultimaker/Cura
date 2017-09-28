# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import VersionUpgrade27to30

upgrade = VersionUpgrade27to30.VersionUpgrade27to30()

def getMetaData():
    return {
        "version_upgrade": {
            # From                    To                       Upgrade function
            ("preferences", 4000002): ("preferences", 5000003, upgrade.upgradePreferences),

            ("machine_stack", 3000002):     ("machine_stack", 3000003,     upgrade.upgradeStack),
            ("extruder_train", 3000002):    ("extruder_train", 3000003,    upgrade.upgradeStack),

            ("quality_changes", 2000002):    ("quality_changes", 2000003,    upgrade.upgradeOtherContainer),
            ("user", 2000002):               ("user", 2000003,               upgrade.upgradeOtherContainer),
            ("quality", 2000002):            ("quality", 2000003,            upgrade.upgradeOtherContainer),
            ("definition_changes", 2000002): ("definition_changes", 2000003, upgrade.upgradeOtherContainer),
            ("variant", 2000002):            ("variant", 2000003,            upgrade.upgradeOtherContainer)
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

def register(app):
    return { "version_upgrade": upgrade }
