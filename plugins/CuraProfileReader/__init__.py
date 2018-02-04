# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import CuraProfileReader

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "profile_reader": [
            {
                "extension": "curaprofile",
                "description": catalog.i18nc("@item:inlistbox", "Cura Profile")
            }
        ]
    }

def register(app):
    return { "profile_reader": CuraProfileReader.CuraProfileReader() }
