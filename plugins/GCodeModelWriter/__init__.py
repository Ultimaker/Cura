# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import GCodeModelWriter

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {


        "mesh_writer": {
            "output": [{
                "extension": "stl",
                "description": catalog.i18nc("@item:inlistbox", "STL File /w gcode as model"),
                "mime_type": "text/x-gcode",
                "mode": GCodeModelWriter.GCodeModelWriter.OutputMode.BinaryMode
            }]
        }
    }

def register(app):
    return { "mesh_writer": GCodeModelWriter.GCodeModelWriter() }
