# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from . import BedLevelMachineAction
from . import UpgradeFirmwareMachineAction
from . import UMOCheckupMachineAction
from . import UMOUpgradeSelection
from . import UM2UpgradeSelection

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "plugin": {
            "name": catalog.i18nc("@label", "Ultimaker machine actions"),
            "author": "Ultimaker",
            "version": "1.0",
            "description": catalog.i18nc("@info:whatsthis", "Provides machine actions for Ultimaker machines (such as bed leveling wizard, selecting upgrades, etc)"),
            "api": 3
        }
    }

def register(app):
    return { "machine_action": [
        BedLevelMachineAction.BedLevelMachineAction(),
        UpgradeFirmwareMachineAction.UpgradeFirmwareMachineAction(),
        UMOCheckupMachineAction.UMOCheckupMachineAction(),
        UMOUpgradeSelection.UMOUpgradeSelection(),
        UM2UpgradeSelection.UM2UpgradeSelection()
    ]}
