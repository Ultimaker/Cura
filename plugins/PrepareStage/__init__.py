# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import PrepareStage

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "stage": {
            "name": i18n_catalog.i18nc("@item:inmenu", "Prepare"),
            "weight": 10
        }
    }

def register(app):
    return {
        "stage": PrepareStage.PrepareStage()
    }
