# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from . import XRayView

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "plugin": {
            "name": catalog.i18nc("@label", "X-Ray View"),
            "author": "Ultimaker",
            "version": "1.0",
            "description": catalog.i18nc("@info:whatsthis", "Provides the X-Ray view."),
            "api": 2
        },
        "view": {
            "name": catalog.i18nc("@item:inlistbox", "X-Ray"),
            "weight": 1
        }
    }

def register(app):
    return { "view": XRayView.XRayView() }
