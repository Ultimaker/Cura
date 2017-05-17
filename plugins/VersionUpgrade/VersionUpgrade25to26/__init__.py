# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from . import VersionUpgrade25to26

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

upgrade = VersionUpgrade25to26.VersionUpgrade25to26()

def getMetaData():
    return {
        "plugin": {
            "name": catalog.i18nc("@label", "Version Upgrade 2.5 to 2.6"),
            "author": "Ultimaker",
            "version": "1.0",
            "description": catalog.i18nc("@info:whatsthis", "Upgrades configurations from Cura 2.5 to Cura 2.6."),
            "api": 3
        },
        "version_upgrade": {
            # From                          To                          Upgrade function
            ("preferences", 4000000):     ("preferences", 4000001,     upgrade.upgradePreferences),
            # NOTE: All the instance containers share the same general/version, so we have to update all of them
            #       if any is updated.
            ("quality_changes", 2000000): ("quality_changes", 2000001, upgrade.upgradeInstanceContainer),
            ("user", 2000000):            ("user", 2000001,            upgrade.upgradeInstanceContainer),
            ("quality", 2000000):         ("quality", 2000001,         upgrade.upgradeInstanceContainer),
        },
        "sources": {
            "quality_changes": {
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
            },
        }
    }

def register(app):
    return { "version_upgrade": upgrade }
