# Copyright (c) 2018 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.

from . import StepReader

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("uranium")

def getMetaData():
    return {
        "mesh_reader": [
            {
                "extension": "step",
                "description": i18n_catalog.i18nc("@item:inlistbox", "STEP File")
            }
        ]
    }

def register(app):
    return { "mesh_reader": StepReader.STEPReader() }
