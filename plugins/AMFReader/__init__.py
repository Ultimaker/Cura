# Copyright (c) 2019 fieldOfView
# Cura is released under the terms of the LGPLv3 or higher.

from . import AMFReader

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("uranium")


def getMetaData():
    return {
        "mesh_reader": [
            {
                "extension": "amf",
                "description": i18n_catalog.i18nc("@item:inlistbox", "AMF File")
            }
        ]
    }

def register(app):
    return {"mesh_reader": AMFReader.AMFReader()}
