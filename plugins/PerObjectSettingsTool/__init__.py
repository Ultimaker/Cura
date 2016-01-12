# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from . import PerObjectSettingsTool

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "plugin": {
            "name": i18n_catalog.i18nc("@label", "Per Object Settings Tool"),
            "author": "Ultimaker",
            "version": "1.0",
            "description": i18n_catalog.i18nc("@info:whatsthis", "Provides the Per Object Settings."),
            "api": 2
        },
        "tool": {
            "name": i18n_catalog.i18nc("@label", "Per Object Settings"),
            "description": i18n_catalog.i18nc("@info:tooltip", "Configure Per Object Settings"),
            "icon": "setting_per_object",
            "tool_panel": "PerObjectSettingsPanel.qml",
            "weight": 3
        },
    }

def register(app):
    return { "tool": PerObjectSettingsTool.PerObjectSettingsTool() }
