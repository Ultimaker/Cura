# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

from . import ThreeMFReader

def getMetaData():
    return {
        "plugin": {
            "name": "3MF Reader",
            "author": "Ultimaker",
            "version": "1.0",
            "description": catalog.i18nc("3MF Reader plugin description", "Provides support for reading 3MF files."),
            "api": 2
        },
        "mesh_reader": {
            "extension": "3mf",
            "description": catalog.i18nc("3MF Reader plugin file type", "3MF File")
        }
    }

def register(app):
    return { "mesh_reader": ThreeMFReader.ThreeMFReader() }
