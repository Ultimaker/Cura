# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from . import VersionUpgrade26to27

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

upgrade = VersionUpgrade26to27.VersionUpgrade26to27()

def getMetaData():
    return {
        "version_upgrade": {
            # From                          To                             Upgrade function
            ("machine_stack", 3000000):     ("machine_stack", 3000002,     upgrade.upgradeStack),
            ("extruder_train", 3000000):    ("extruder_train", 3000002,    upgrade.upgradeStack),
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
