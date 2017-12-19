# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import VersionUpgrade31to32

upgrade = VersionUpgrade31to32.VersionUpgrade31to32()

def getMetaData():
    return {
        "version_upgrade": {
                    # From                    To                       Upgrade function

            ("preferences", 5000004):       ("preferences", 5000005, upgrade.upgradePreferences),

            ("machine_stack", 3000004):     ("machine_stack", 3000005, upgrade.upgradeStack),
            ("extruder_train", 3000004):    ("extruder_train", 3000005, upgrade.upgradeStack),

            ("quality_changes", 2000004):   ("quality_changes", 2000005, upgrade.upgradeInstanceContainer),
            ("user", 2000004):              ("user", 2000005, upgrade.upgradeInstanceContainer),
            ("quality", 2000004):           ("quality", 2000005, upgrade.upgradeInstanceContainer),
            ("definition_changes", 2000004): ("definition_changes", 2000005, upgrade.upgradeInstanceContainer),
            ("variant", 2000004):           ("variant", 2000005, upgrade.upgradeInstanceContainer)

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
