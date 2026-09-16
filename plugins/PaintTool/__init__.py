# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from . import PaintTool
from . import PaintView

from PyQt6.QtQml import qmlRegisterUncreatableType

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "tool": {
            "name": i18n_catalog.i18nc("@action:button", "Paint"),
            "description": i18n_catalog.i18nc("@info:tooltip", "Paint Model"),
            "icon": "Brush",
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
    qmlRegisterUncreatableType(PaintTool.PaintTool.Brush, "Cura", 1, 0, "This is an enumeration class", "PaintToolBrush")
    qmlRegisterUncreatableType(PaintTool.PaintTool.Paint, "Cura", 1, 0, "This is an enumeration class", "PaintToolState")
    view = PaintView.PaintView()
    return {
        "tool": PaintTool.PaintTool(view),
        "view": view
    }
