# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from . import VersionUpgrade24to25

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

upgrade = VersionUpgrade24to25.VersionUpgrade24to25()

def getMetaData():
    return {
        "plugin": {
            "name": catalog.i18nc("@label", "Version Upgrade 2.4 to 2.5"),
            "author": "Ultimaker",
            "version": "1.0",
            "description": catalog.i18nc("@info:whatsthis", "Upgrades configurations from Cura 2.4 to Cura 2.5."),
            "api": 3
        },
        "version_upgrade": {
            # From              To                 Upgrade function
            ("preferences", 4): ("preferences", 5, upgrade.upgradePreferences),
            ("quality", 2):     ("quality", 3,     upgrade.upgradeInstanceContainer),
            ("variant", 2):     ("variant", 3,     upgrade.upgradeInstanceContainer), #We can re-use upgradeContainerStack since there is nothing specific to quality, variant or user profiles being changed.
            ("user", 2):        ("user", 3,        upgrade.upgradeInstanceContainer)
        },
        "sources": {
            "quality": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./quality"}
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
    return {}
    return { "version_upgrade": upgrade }
