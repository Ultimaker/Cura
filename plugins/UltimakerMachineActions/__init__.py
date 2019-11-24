# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import BedLevelMachineAction
from . import UMOUpgradeSelection

def getMetaData():
    return {}

def register(app):
    return { "machine_action": [
        BedLevelMachineAction.BedLevelMachineAction(),
        UMOUpgradeSelection.UMOUpgradeSelection()
    ]}
