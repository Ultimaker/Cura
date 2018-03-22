# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import GCodeGzReader

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "mesh_reader": [
            {
                "extension": "gcode.gz",
                "description": i18n_catalog.i18nc("@item:inlistbox", "Compressed G-code File")
            }
        ]
    }

def register(app):
    app.addNonSliceableExtension(".gcode.gz")
    return { "mesh_reader": GCodeGzReader.GCodeGzReader() }
