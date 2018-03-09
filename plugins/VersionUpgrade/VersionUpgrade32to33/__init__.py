# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import VersionUpgrade32to33

upgrade = VersionUpgrade32to33.VersionUpgrade32to33()

def getMetaData():
    return {
        "version_upgrade": {
            # From                        To                   Upgrade function
            ("quality_changes", 2000004): ("quality_changes", 3000004, upgrade.upgradeQualityChanges),
        },
        "sources": {
            "quality_changes": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./quality"}
            }
        }
    }

def register(app):
    return { "version_upgrade": upgrade }