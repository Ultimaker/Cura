# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from . import CuraProfileWriter

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "plugin": {
            "name": catalog.i18nc("@label", "Cura Profile Writer"),
            "author": "Ultimaker",
            "version": "1.0",
            "description": catalog.i18nc("@info:whatsthis", "Provides support for exporting Cura profiles."),
            "api": 2
        },
        "profile_writer": [
            {
                "extension": "curaprofile",
                "description": catalog.i18nc("@item:inlistbox", "Cura Profile")
            }
        ]
    }

def register(app):
    return { "profile_writer": CuraProfileWriter.CuraProfileWriter() }
