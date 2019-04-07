# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.i18n import i18nCatalog
from UM.Platform import Platform

from . import GCodeGzWriter

catalog = i18nCatalog("cura")

def getMetaData():
    file_extension = "gcode.gz"
    return {
        "mesh_writer": {
            "output": [{
                "extension": file_extension,
                "description": catalog.i18nc("@item:inlistbox", "Compressed G-code File"),
                "mime_type": "application/gzip",
                "mode": GCodeGzWriter.GCodeGzWriter.OutputMode.BinaryMode,
                "hide_in_file_dialog": True,
            }]
        }
    }

def register(app):
    return { "mesh_writer": GCodeGzWriter.GCodeGzWriter() }
