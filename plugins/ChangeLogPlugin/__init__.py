# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.
from UM.i18n import i18nCatalog

from . import ChangeLog

catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "plugin": {
            "name": "Change log",
            "author": "Ultimaker",
            "version": "1.0",
            "description": catalog.i18nc("Change log plugin description", "Shows changes since latest checked version"),
            "api": 2
        }
    }

def register(app):
    return {"extension": ChangeLog.ChangeLog()}