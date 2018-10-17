# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import FirmwareUpdaterMachineAction

def getMetaData():
    return {}

def register(app):
    return { "machine_action": [
        FirmwareUpdaterMachineAction.FirmwareUpdaterMachineAction()
    ]}
