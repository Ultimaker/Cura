# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import GCodeGzWriter

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "mesh_writer": {
            "output": [{
                "extension": "gcode.gz",
                "description": catalog.i18nc("@item:inlistbox", "Compressed G-code File"),
                "mime_type": "application/gzip",
                "mode": GCodeGzWriter.GCodeGzWriter.OutputMode.BinaryMode
            }]
        }
    }

def register(app):
    return { "mesh_writer": GCodeGzWriter.GCodeGzWriter() }
