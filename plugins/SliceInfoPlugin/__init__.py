# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.
from . import SliceInfo
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "plugin": {
            "name": "Slice Info",
            "author": "Ultimaker",
            "version": "1.0",
            "description": catalog.i18nc("Slice Info plugin description", "Submits anonymous slice info. Can be disabled through preferences."),
            "api": 2
        }
    }

def register(app):
    return { "extension": SliceInfo.SliceInfo()}