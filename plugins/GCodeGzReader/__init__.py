# Copyright (c) 2016 Aleph Objects, Inc.
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
    app.addNonSliceableExtension(".gz")  # in some parts only the last extension is taken. Let's make it a non sliceable extension for now
    return { "mesh_reader": GCodeGzReader.GCodeGzReader() }
