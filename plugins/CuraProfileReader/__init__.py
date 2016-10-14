# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from . import CuraProfileReader

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "plugin": {
            "name": catalog.i18nc("@label", "Cura Profile Reader"),
            "author": "Ultimaker",
            "version": "1.0",
            "description": catalog.i18nc("@info:whatsthis", "Provides support for importing Cura profiles."),
            "api": 3
        },
        "profile_reader": [
            {
                "extension": "curaprofile",
                "description": catalog.i18nc("@item:inlistbox", "Cura Profile")
            }
        ]
    }

def register(app):
    return { "profile_reader": CuraProfileReader.CuraProfileReader() }
