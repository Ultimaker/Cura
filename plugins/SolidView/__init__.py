# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from . import SolidView

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "plugin": {
            "name": i18n_catalog.i18nc("@label", "Solid View"),
            "author": "Ultimaker",
            "version": "1.0",
            "decription": i18n_catalog.i18nc("@info:whatsthis", "Provides a normal solid mesh view."),
            "api": 2
        },
        "view": {
            "name": i18n_catalog.i18nc("@item:inmenu", "Solid"),
            "weight": 0
        }
    }

def register(app):
    return { "view": SolidView.SolidView() }
