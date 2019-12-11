# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from .src import UM3OutputDevicePlugin
from .src import UltimakerNetworkedPrinterAction


def getMetaData():
    return {}


def register(app):
    return {
        "output_device": UM3OutputDevicePlugin.UM3OutputDevicePlugin(),
        "machine_action": UltimakerNetworkedPrinterAction.UltimakerNetworkedPrinterAction()
    }
