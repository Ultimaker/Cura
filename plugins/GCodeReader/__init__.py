# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

from . import GCodeReader

def getMetaData():
    return {
        "plugin": {
            "name": catalog.i18nc("@label", "GCode Reader"),
            "author": "Ultimaker",
            "version": "1.0",
            "description": catalog.i18nc("@info:whatsthis", "Provides support for reading GCode files."),
            "api": 2
        },
        "mesh_reader": {
            "extension": "gcode",
            "description": catalog.i18nc("@item:inlistbox", "Gcode File")
        }
    }

def register(app):
    return { "mesh_reader": GCodeReader.GCodeReader() }
