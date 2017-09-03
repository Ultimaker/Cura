from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

from UM.Logger import Logger
from UM.Platform import Platform

def getMetaData():
    return {
        "plugin": {
            "name": catalog.i18nc("@label", "Power Management"),
            "author": "Thomas Karl Pietrowski",
            "version": "0.0.1",
            "description": catalog.i18nc("@info:whatsthis",
                                         "Manages powersaving settings on the current system"),
            "api": 3
        }
    }

def register(app):
    if Platform.isLinux():
        from . import PowerManagementLinux
        return { "extension": PowerManagementLinux.PowerManagement() }
    elif Platform.isWindows():
        from . import PowerManagementWindows
        return { "extension": PowerManagementWindows.PowerManagement() }
    elif Platform.isOSX():
        from . import PowerManagementOSX
        return { "extension": PowerManagementOSX.PowerManagement() }
    
    Logger.log("e", "Your operating system is currently not supported.")
    return { }