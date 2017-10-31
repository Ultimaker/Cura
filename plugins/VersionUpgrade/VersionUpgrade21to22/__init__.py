# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from . import VersionUpgrade21to22

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

upgrade = VersionUpgrade21to22.VersionUpgrade21to22()

def getMetaData():
    return {
        "plugin": {
            "name": catalog.i18nc("@label", "Version Upgrade 2.1 to 2.2"),
            "author": "Ultimaker",
            "version": "1.0",
            "description": catalog.i18nc("@info:whatsthis", "Upgrades configurations from Cura 2.1 to Cura 2.2."),
            "api": 3
        },
        "version_upgrade": {
            # From                         To                         Upgrade function
            ("profile", 1000000):          ("quality", 2000000,       upgrade.upgradeProfile),
            ("machine_instance", 1000000): ("machine_stack", 2000000, upgrade.upgradeMachineInstance),
            ("preferences", 2000000):      ("preferences", 3000000,   upgrade.upgradePreferences)
        },
        "sources": {
            "profile": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./profiles", "./instance_profiles"}
            },
            "machine_instance": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./machine_instances"}
            },
            "preferences": {
                "get_version": upgrade.getCfgVersion,
                "location": {"."}
            },
            "user": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./user"}
            }
        }
    }

def register(app):
    return { "version_upgrade": upgrade }
