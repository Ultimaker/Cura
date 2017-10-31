# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import VersionUpgrade25to26

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

upgrade = VersionUpgrade25to26.VersionUpgrade25to26()

def getMetaData():
    return {
        "version_upgrade": {
            # From                          To                          Upgrade function
            ("preferences", 4000000):     ("preferences", 4000001,     upgrade.upgradePreferences),
            # NOTE: All the instance containers share the same general/version, so we have to update all of them
            #       if any is updated.
            ("quality_changes", 2000000):       ("quality_changes", 2000001,    upgrade.upgradeInstanceContainer),
            ("user", 2000000):                  ("user", 2000001,               upgrade.upgradeInstanceContainer),
            ("quality", 2000000):               ("quality", 2000001,            upgrade.upgradeInstanceContainer),
            ("definition_changes", 2000000):    ("definition_changes", 2000001, upgrade.upgradeInstanceContainer),
            ("machine_stack", 3000000):         ("machine_stack", 3000001,      upgrade.upgradeMachineStack),
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
            "definition_changes": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./machine_instances"}
            },
            "machine_stack": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./machine_instances"}
            }
        }
    }

def register(app):
    return { "version_upgrade": upgrade }
