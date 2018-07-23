# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import ImageReader

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "mesh_reader": [
            {
                "extension": "jpg",
                "description": i18n_catalog.i18nc("@item:inlistbox", "JPG Image")
            },
            {
                "extension": "jpeg",
                "description": i18n_catalog.i18nc("@item:inlistbox", "JPEG Image")
            },
            {
                "extension": "png",
                "description": i18n_catalog.i18nc("@item:inlistbox", "PNG Image")
            },
            {
                "extension": "bmp",
                "description": i18n_catalog.i18nc("@item:inlistbox", "BMP Image")
            },
            {
                "extension": "gif",
                "description": i18n_catalog.i18nc("@item:inlistbox", "GIF Image")
            }
        ]
    }


def register(app):
    return {"mesh_reader": ImageReader.ImageReader()}
