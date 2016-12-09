# Copyright (c) 2016 Aleph Objects, Inc.
# Cura is released under the terms of the AGPLv3 or higher.

from . import GCodeReader

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "plugin": {
            "name": i18n_catalog.i18nc("@label", "G-code Reader"),
            "author": "Victor Larchenko",
            "version": "1.0",
            "description": i18n_catalog.i18nc("@info:whatsthis", "Allows loading and displaying G-code files."),
            "api": 3
        },
        "mesh_reader": [
            {
                "extension": "gcode",
                "description": i18n_catalog.i18nc("@item:inlistbox", "G-code File")
            },
            {
                "extension": "g",
                "description": i18n_catalog.i18nc("@item:inlistbox", "G File")
            }
        ]
    }

def register(app):
    app.non_sliceable_extensions.append(".gcode")
    app.non_sliceable_extensions.append(".g")
    return { "mesh_reader": GCodeReader.GCodeReader() }
