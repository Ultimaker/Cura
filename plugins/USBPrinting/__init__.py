# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import USBPrinterOutputDeviceManager


def getMetaData():
    return {}


def register(app):
    # USBPrinting plugin disabled: do not register any output devices
    return {}
