# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

import platform

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "plugin": {
            "name": catalog.i18nc("@label", "Removable Drive Output Device Plugin"),
            "author": "Ultimaker B.V.",
            "description": catalog.i18nc("@info:whatsthis", "Provides removable drive hotplugging and writing support."),
            "version": "1.0",
            "api": 2
        }
    }

def register(app):
    if platform.system() == "Windows":
        from . import WindowsRemovableDrivePlugin
        return { "output_device": WindowsRemovableDrivePlugin.WindowsRemovableDrivePlugin() }
    elif platform.system() == "Darwin":
        from . import OSXRemovableDrivePlugin
        return { "output_device": OSXRemovableDrivePlugin.OSXRemovableDrivePlugin() }
    elif platform.system() == "Linux":
        from . import LinuxRemovableDrivePlugin
        return { "output_device": LinuxRemovableDrivePlugin.LinuxRemovableDrivePlugin() }
    else:
        Logger.log("e", "Unsupported system %s, no removable device hotplugging support available.", platform.system())
        return { }
