# Copyright (c) 2017 Ultimaker B.V.
from PyQt5.QtCore import QUrl

from UM.Logger import Logger
from UM.PluginObject import PluginObject
from UM.PluginRegistry import PluginRegistry

#   Abstract class for sidebar view objects.
#   By default the sidebar is Cura's settings, slicing and printing overview.
#   The last plugin to claim the sidebar QML target will be displayed.
class SidebarView(PluginObject):

    def __init__(self):
        super().__init__()
        self._view = None

    ##  Get the path to the component QML file as QUrl
    def getComponentPath(self):
        try:
            sidebar_component_file_path = PluginRegistry.getInstance().getMetaData(self.getPluginId())["sidebar_view"]["sidebar_component"]
            return QUrl.fromLocalFile(sidebar_component_file_path)
        except KeyError:
            Logger.log("w", "Could not find sidebar component QML file for %s", self.getPluginId())
            return QUrl()
