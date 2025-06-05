# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from . import PaintTool
from . import PaintView

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "tool": {
            "name": i18n_catalog.i18nc("@action:button", "Paint"),
            "description": i18n_catalog.i18nc("@info:tooltip", "Paint Model"),
            "icon": "Visual",
            "tool_panel": "PaintTool.qml",
            "weight": 0
        },
        "view": {
            "name": i18n_catalog.i18nc("@item:inmenu", "Paint view"),
            "weight": 0,
            "visible": False
        }
    }

def register(app):
    return {
        "tool": PaintTool.PaintTool(),
        "view": PaintView.PaintView()
    }
