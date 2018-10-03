# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import USBPrinterOutputDeviceManager


def getMetaData():
    return {}


def register(app):
    # We are violating the QT API here (as we use a factory, which is technically not allowed).
    # but we don't really have another means for doing this (and it seems to you know -work-)
    return {"output_device": USBPrinterOutputDeviceManager.USBPrinterOutputDeviceManager(app)}
