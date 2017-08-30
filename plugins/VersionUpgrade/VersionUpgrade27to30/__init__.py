# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from . import VersionUpgrade27to30

upgrade = VersionUpgrade27to30.VersionUpgrade27to30()

def getMetaData():
    return {
        "version_upgrade": {
            # From                    To                       Upgrade function
            ("preferences", 4000002): ("preferences", 5000002, upgrade.upgradePreferences),
        },
        "sources": {
            "preferences": {
                "get_version": upgrade.getCfgVersion,
                "location": {"."}
            },
        }
    }

def register(app):
    return { "version_upgrade": upgrade }
