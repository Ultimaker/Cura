# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.

from . import PerObjectSettingsTool
from . import PerObjectSettingVisibilityHandler
from PyQt5.QtQml import qmlRegisterType

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "tool": {
            "name": i18n_catalog.i18nc("@label", "Per Model Settings"),
            "description": i18n_catalog.i18nc("@info:tooltip", "Configure Per Model Settings"),
            "icon": "MeshType",
            "tool_panel": "PerObjectSettingsPanel.qml",
            "weight": 3
        },
    }

def register(app):
    qmlRegisterType(PerObjectSettingVisibilityHandler.PerObjectSettingVisibilityHandler, "Cura", 1, 0,
                    "PerObjectSettingVisibilityHandler")
    return { "tool": PerObjectSettingsTool.PerObjectSettingsTool() }
