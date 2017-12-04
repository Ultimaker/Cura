# Copyright (c) 2017 Ultimaker B.V.
import os.path

from UM.Application import Application
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

    def getComponent(self):
        if not self._view:
            self.createView()
        return self._view

    def createView(self):
        component_path = self.getComponentPath()
        self._view = Application.getInstance().createQmlComponent(component_path, {"manager": self})

    ##  Get the path to the component QML file as QUrl
    def getComponentPath(self):
        try:
            plugin_path = PluginRegistry.getInstance().getPluginPath(self.getPluginId())
            sidebar_component_file_path = PluginRegistry.getInstance().getMetaData(self.getPluginId())["sidebar_view"]["sidebar_component"]
            return os.path.join(plugin_path, sidebar_component_file_path)
        except KeyError:
            Logger.log("w", "Could not find sidebar component QML file for %s", self.getPluginId())
            return ""
