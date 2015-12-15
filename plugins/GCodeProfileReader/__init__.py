# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from . import GCodeProfileReader

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "plugin": {
            "name": catalog.i18nc("@label", "GCode Profile Reader"),
            "author": "Ultimaker",
            "version": "1.0",
            "description": catalog.i18nc("@info:whatsthis", "Provides support for importing profiles from g-code files."),
            "api": 2
        },
        "profile_reader": [
            {
                "extension": "gcode",
                "description": catalog.i18nc("@item:inlistbox", "G-code File")
            }
        ]
    }

def register(app):
    return { "profile_reader": GCodeProfileReader.GCodeProfileReader() }
