# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import PreviewStage

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")


def getMetaData():
    return {
        "stage": {
            "name": i18n_catalog.i18nc("@item:inmenu", "Preview"),
            "weight": 20
        }
    }


def register(app):
    return {
        "stage": PreviewStage.PreviewStage(app)
    }
