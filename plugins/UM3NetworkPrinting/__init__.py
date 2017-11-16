# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from . import NetworkPrinterOutputDevicePlugin
from . import DiscoverUM3Action
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {}

def register(app):
    return { "output_device": NetworkPrinterOutputDevicePlugin.NetworkPrinterOutputDevicePlugin(), "machine_action": DiscoverUM3Action.DiscoverUM3Action()}