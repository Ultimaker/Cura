# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import BedLevelMachineAction
from . import UpgradeFirmwareMachineAction
from . import UMOCheckupMachineAction
from . import UMOUpgradeSelection
from . import UM2UpgradeSelection

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
    }

def register(app):
    return { "machine_action": [
        BedLevelMachineAction.BedLevelMachineAction(),
        UpgradeFirmwareMachineAction.UpgradeFirmwareMachineAction(),
        UMOCheckupMachineAction.UMOCheckupMachineAction(),
        UMOUpgradeSelection.UMOUpgradeSelection(),
        UM2UpgradeSelection.UM2UpgradeSelection()
    ]}
