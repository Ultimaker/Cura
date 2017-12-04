# Copyright (c) 2017 Ultimaker B.V.
from UM.Logger import Logger
from UM.Preferences import Preferences
from UM.Signal import Signal
from UM.PluginRegistry import PluginRegistry

# The sidebar controller manages available sidebar components and decides which one to display.
# The cura.qml file uses this controller to repeat over the sidebars and show the active index.
class SidebarController:

    def __init__(self, application):
        self._application = application
        self._sidebar_views = {}
        self._active_sidebar_view = None

        # Register the sidebar_view plugin type so plugins can expose custom sidebar views.
        PluginRegistry.addType("sidebar_view", self.addSidebarView)

    ##  Emitted when the list of views changes.
    sidebarViewsChanged = Signal()

    ##  Emitted when the active view changes.
    activeSidebarViewChanged = Signal()

    ##  Get the active application instance.
    def getApplication(self):
        return self._application

    ##  Get all sidebar views registered in this controller.
    def getAllSidebarViews(self):
        return self._sidebar_views

    ##  Add a sidebar view to the registry.
    #   It get's a unique name based on the plugin ID.
    def addSidebarView(self, sidebar_view):
        sidebar_view_id = sidebar_view.getPluginId()
        if sidebar_view_id not in self._sidebar_views:
            self._sidebar_views[sidebar_view_id] = sidebar_view
            self.sidebarViewsChanged.emit()

    ##  Get a registered sidebar view by name.
    #   The name is the ID of the plugin that registered the view.
    def getSidebarView(self, name: str):
        try:
            return self._sidebar_views[name]
        except KeyError:
            Logger.log("e", "Unable to find %s in sidebar view list", name)
            return None

    ##  Get the active sidebar view.
    def getActiveSidebarView(self):
        return self._active_sidebar_view

    ##  Change the active sidebar view to one of the registered views.
    def setActiveSidebarView(self, sidebar_view_id: str):
        if sidebar_view_id in self._sidebar_views:
            self._active_sidebar_view = self._sidebar_views[sidebar_view_id]
            Preferences.getInstance().setValue("cura/active_sidebar_view", sidebar_view_id)
            self.activeSidebarViewChanged.emit()
