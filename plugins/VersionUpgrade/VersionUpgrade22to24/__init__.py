# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import VersionUpgrade

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

upgrade = VersionUpgrade.VersionUpgrade22to24()

def getMetaData():
    return {
        "version_upgrade": {
            # From                         To                 Upgrade function
            ("machine_instance", 2000000): ("machine_stack",  3000000, upgrade.upgradeMachineInstance),
            ("extruder_train", 2000000):   ("extruder_train", 3000000, upgrade.upgradeExtruderTrain),
            ("preferences", 3000000):      ("preferences",    4000000, upgrade.upgradePreferences),
            ("quality", 2000000):          ("quality_changes", 2000000, upgrade.upgradeQuality),
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
        }
    }

def register(app):
    return { "version_upgrade": upgrade }
