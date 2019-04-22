#Copyright (c) 2019 Ultimaker B.V.
#Cura is released under the terms of the LGPLv3 or higher.

from UM.i18n import i18nCatalog

from . import UFPReader

i18n_catalog = i18nCatalog("cura")


def getMetaData():
    return {
        "mesh_reader": [
            {
                "mime_type": "application/x-ufp",
                "extension": "ufp",
                "description": i18n_catalog.i18nc("@item:inlistbox", "Ultimaker Format Package")
            }
        ]
    }


def register(app):
    app.addNonSliceableExtension(".ufp")
    return {"mesh_reader": UFPReader.UFPReader()}

