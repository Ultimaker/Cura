# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import BedLevelMachineAction
from . import UMOUpgradeSelection
from . import UM2UpgradeSelection

def getMetaData():
    return {}

def register(app):
    return { "machine_action": [
        BedLevelMachineAction.BedLevelMachineAction(),
        UMOUpgradeSelection.UMOUpgradeSelection(),
        UM2UpgradeSelection.UM2UpgradeSelection()
    ]}
