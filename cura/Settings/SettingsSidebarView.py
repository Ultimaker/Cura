# Copyright (c) 2017 Ultimaker B.V.
from PyQt5.QtCore import QObject

from UM.i18n import i18nCatalog

from cura.Sidebar.SidebarView import SidebarView
i18n_catalog = i18nCatalog("cura")

class SettingsSidebarView(QObject, SidebarView):

    def __init__(self, parent = None):
        super().__init__(parent)

    ##  As the default sidebar is not a plugin, we have a get plugin ID method to allow the sidebar view model to get the needed data.
    def getPluginId(self):
        return "default"

    ##  As the default sidebar is not a plugin, we have a add meta data method here to allow the sidebar view model to get the needed data.
    def getMetaData(self):
        return {
            "sidebar_view": {
                "name": i18n_catalog.i18nc("@item:inmenu", "Print settings"),
                "weight": 0
            }
        }

    def getComponent(self):
        return None
