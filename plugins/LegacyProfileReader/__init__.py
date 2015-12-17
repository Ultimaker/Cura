# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from . import LegacyProfileReader

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "plugin": {
            "name": catalog.i18nc("@label", "Legacy Cura Profile Reader"),
            "author": "Ultimaker",
            "version": "1.0",
            "description": catalog.i18nc("@info:whatsthis", "Provides support for importing profiles from legacy Cura versions."),
            "api": 2
        },
        "profile_reader": [
            {
                "extension": "ini",
                "description": catalog.i18nc("@item:inlistbox", "Cura 15.04 profiles")
            }
        ]
    }

def register(app):
    return { "profile_reader": LegacyProfileReader.LegacyProfileReader() }
