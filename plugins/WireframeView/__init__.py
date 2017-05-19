# Copyright (c) 2017 Tim Kuipers
# Cura is released under the terms of the AGPLv3 or higher.

from . import WireframeView

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "plugin": {
            "name": catalog.i18nc("@label", "Wireframe View"),
            "author": "Tim Kuipers",
            "version": "1.0",
            "description": catalog.i18nc("@info:whatsthis", "Provides the Wireframe view."),
            "api": 3
        },
        "view": {
            "name": catalog.i18nc("@item:inlistbox", "Wireframe"),
            "weight": 1
        }
    }

def register(app):
    return { "view": WireframeView.WireframeView() }
