# Copyright (c) 2017 Ultimaker B.V.
from UM.Logger import Logger
from UM.PluginRegistry import PluginRegistry
from UM.Signal import Signal
from .SidebarView import SidebarView
from typing import Optional, Dict

# The sidebar controller manages available sidebar components and decides which one to display.
# The cura.qml file uses this controller to repeat over the sidebars and show the active index.
class SidebarController:

    def __init__(self, application):
        self._application = application
        self._sidebar_views = {}
        self._active_sidebar_view = None

        PluginRegistry.addType("sidebar_view", self.addSidebarView)

    ##  Emitted when the list of views changes.
    sidebarViewsChanged = Signal()

    ##  Emitted when the active view changes.
    activeSidebarViewChanged = Signal()

    ##  Get the active application instance.
    def getApplication(self):
        return self._application

    ##  Add a sidebar view to the registry.
    #   It get's a unique name based on the plugin ID.
    def addSidebarView(self, sidebar_view: SidebarView):
        name = sidebar_view.getPluginId()
        if name not in self._sidebar_views:
            self._sidebar_views[name] = sidebar_view
            self.sidebarViewsChanged.emit()

    ##  Get a registered sidebar view by name.
    #   The name is the ID of the plugin that registered the view.
    def getSidebarView(self, name: str) -> Optional[SidebarView]:
        try:
            return self._sidebar_views[name]
        except KeyError:
            Logger.log("e", "Unable to find %s in sidebar view list", name)
            return None

    ##  Change the active sidebar view to one of the registered views.
    def setActiveSidebarView(self, name: str):
        print("setting active sidebar view")

    ##  Get all sidebar views registered in this controller.
    def getAllSidebarViews(self) -> Dict[SidebarView]:
        return self._sidebar_views
