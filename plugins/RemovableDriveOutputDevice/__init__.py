# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Platform import Platform
from UM.Logger import Logger


def getMetaData():
    return {}

def register(app):
    if Platform.isWindows():
        from . import WindowsRemovableDrivePlugin
        return { "output_device": WindowsRemovableDrivePlugin.WindowsRemovableDrivePlugin() }
    elif Platform.isOSX():
        from . import OSXRemovableDrivePlugin
        return { "output_device": OSXRemovableDrivePlugin.OSXRemovableDrivePlugin() }
    elif Platform.isLinux():
        from . import LinuxRemovableDrivePlugin
        return { "output_device": LinuxRemovableDrivePlugin.LinuxRemovableDrivePlugin() }
    else:
        Logger.log("e", "Unsupported system, thus no removable device hotplugging support available.")
        return { }
