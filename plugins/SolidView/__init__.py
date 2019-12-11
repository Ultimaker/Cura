# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import SolidView

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "view": {
            "name": i18n_catalog.i18nc("@item:inmenu", "Solid view"),
            "weight": 0,
            "visible": False
        }
    }

def register(app):
    return { "view": SolidView.SolidView() }
