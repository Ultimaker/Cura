# Copyright (c) 2019 Ultimaker
# Cura is released under the terms of the LGPLv3 or higher.

from . import PLYReader

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("uranium")


def getMetaData():
    return {
        "mesh_reader": [
            {
                "extension": "ply",
                "description": i18n_catalog.i18nc("@item:inlistbox", "PLY File")
            }
        ]
    }

def register(app):
    return {"mesh_reader": PLYReader.PLYReader()}
