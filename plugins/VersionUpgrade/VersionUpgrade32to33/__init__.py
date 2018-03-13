# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import VersionUpgrade32to33

upgrade = VersionUpgrade32to33.VersionUpgrade32to33()

def getMetaData():
    return {
        "version_upgrade": {
            # From                           To                              Upgrade function
            ("definition_changes", 2000004): ("definition_changes", 3000004, upgrade.upgradeInstanceContainer),
            ("quality_changes", 2000004):    ("quality_changes", 3000004,    upgrade.upgradeQualityChanges),
            ("user", 2000004):               ("user", 3000004,               upgrade.upgradeInstanceContainer)
        },
        "sources": {
            "definition_changes": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./definition_changes"}
            },
            "quality_changes": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./quality"}
            },
            "user": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./user"}
            }
        }
    }

def register(app):
    return { "version_upgrade": upgrade }