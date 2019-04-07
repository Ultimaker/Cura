# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from . import MonitorStage


from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")


def getMetaData():
    return {
        "stage": {
            "name": i18n_catalog.i18nc("@item:inmenu", "Monitor"),
            "weight": 2
        }
    }


def register(app):
    return {
        "stage": MonitorStage.MonitorStage()
    }
