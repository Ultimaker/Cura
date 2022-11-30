#  Copyright (c) 2022 UltiMaker
#  Cura is released under the terms of the LGPLv3 or higher.

import sys

from UM.Logger import Logger
try:
    from . import UFPReader
except ImportError:
    Logger.log("w", "Could not import UFPReader; libCharon may be missing")

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")


def getMetaData():
    return {
        "mesh_reader": [
            {
                "mime_type": "application/x-ufp",
                "extension": "ufp",
                "description": i18n_catalog.i18nc("@item:inlistbox", "UltiMaker Format Package")
            }
        ]
    }


def register(app):
    if "UFPReader.UFPReader" not in sys.modules:
        return {}

    app.addNonSliceableExtension(".ufp")
    return {"mesh_reader": UFPReader.UFPReader()}

