# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from . import VersionUpgrade

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

upgrade = VersionUpgrade.VersionUpgrade22to24()

def getMetaData():
    return {
        "plugin": {
            "name": catalog.i18nc("@label", "Version Upgrade 2.2 to 2.4"),
            "author": "Ultimaker",
            "version": "1.0",
            "description": catalog.i18nc("@info:whatsthis", "Upgrades configurations from Cura 2.2 to Cura 2.4."),
            "api": 3
        },
        "version_upgrade": {
            # From                     To                 Upgrade function
            ("machine_instance", 2): ("machine_stack", 3, upgrade.upgradeMachineInstance),
            ("extruder_train", 2): ("extruder_train", 3, upgrade.upgradeExtruderTrain),
            ("preferences", 3):      ("preferences", 4, upgrade.upgradePreferences)

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
