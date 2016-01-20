# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from . import GCodeWriter

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "plugin": {
            "name": catalog.i18nc("@label", "GCode Writer"),
            "author": "Ultimaker",
            "version": "1.0",
            "description": catalog.i18nc("@info:whatsthis", "Writes GCode to a file"),
            "api": 2
        },

        "backend_output_writer": {
            "output": [{
                "extension": "gcode",
                "description": catalog.i18nc("@item:inlistbox", "GCode File"),
                "mime_type": "text/x-gcode"
            }]
        }
    }

def register(app):
    return { "backend_output_writer": GCodeWriter.GCodeWriter() }
