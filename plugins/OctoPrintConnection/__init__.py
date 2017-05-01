# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.
from . import OctoPrintOutputDevicePlugin
from . import DiscoverOctoPrintAction
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "type": "extension",
        "plugin": {
            "name": "OctoPrint connection",
            "author": "fieldOfView",
            "version": "master",
            "description": catalog.i18nc("@info:whatsthis", "Allows sending prints to OctoPrint and monitoring the progress"),
            "api": 3
        }
    }

def register(app):
    return {
        "output_device": OctoPrintOutputDevicePlugin.OctoPrintOutputDevicePlugin(),
        "machine_action": DiscoverOctoPrintAction.DiscoverOctoPrintAction()
    }