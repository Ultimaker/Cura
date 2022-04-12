# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.i18n import i18nCatalog
from . import StructureView

catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "view": {
            "name": catalog.i18nc("@item:inlistbox", "Structure view"),
            "weight": 1
        }
    }

def register(application):
    return { "view": StructureView.StructureView() }