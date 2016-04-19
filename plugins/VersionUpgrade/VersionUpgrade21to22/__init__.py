# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from . import VersionUpgrade21to22

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "plugin": {
            "name": catalog.i18nc("@label", "Version Upgrade 2.1 to 2.2"),
            "author": "Ultimaker",
            "version": "1.0",
            "description": catalog.i18nc("@info:whatsthis", "Upgrades configurations from Cura 2.1 to Cura 2.2."),
            "api": 2
        },
        "version_upgrade": {
            "profile": {
                "from": 1,
                "to": 2
            },
            "preferences": {
                "from": 2,
                "to": 3
            },
            "machine_instance": {
                "from": 1,
                "to": 2
            }
        }
    }

def register(app):
    return { "version_upgrade": VersionUpgrade21to22.VersionUpgrade21to22() }
