# Copyright (c) 2016 Aldo Hoeben / fieldOfView.
# Cura is released under the terms of the AGPLv3 or higher.

from . import PauseBackend

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "plugin": {
            "name": catalog.i18nc("@label", "Auto Save"),
            "author": "Ultimaker",
            "version": "2.3",
            "description": catalog.i18nc("@info:whatsthis", "Adds a button to pause automatic background slicing."),
            "api": 3
        },
    }

def register(app):
    return { "extension": PauseBackend.PauseBackend() }
