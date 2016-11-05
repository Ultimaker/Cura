# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

#Shoopdawoop
from . import GCODEReader

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("uranium")

def getMetaData():
    return {
        "plugin": {
            "name": i18n_catalog.i18nc("@label", "GCODE Reader"),
            "author": "Victor Larchenko",
            "version": "1.0",
            "description": i18n_catalog.i18nc("@info:whatsthis", "Makes it possbile to read GCODE files."),
            "api": 3
        },
        "mesh_reader": [
            {
                "extension": "gcode",
                "description": i18n_catalog.i18nc("@item:inlistbox", "GCODE File")
            },
            {
                "extension": "g",
                "description": i18n_catalog.i18nc("@item:inlistbox", "G File")
            }
        ]
    }

def register(app):
    return { "mesh_reader": GCODEReader.GCODEReader() }
