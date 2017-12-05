# Copyright (c) 2017 Ultimaker B.V.
from PyQt5.QtCore import Qt
from UM.Qt.ListModel import ListModel
from UM.Application import Application
from UM.PluginRegistry import PluginRegistry

##  The SidebarViewModel is the default sidebar view in Cura with all the print settings and print button.
class SidebarViewModel(ListModel):
    IdRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    ActiveRole = Qt.UserRole + 3

    def __init__(self, parent = None):
        super().__init__(parent)

        # connect views changed signals
        self._controller = Application.getInstance().getSidebarController()
        self._controller.sidebarViewsChanged.connect(self._onSidebarViewsChanged)
        self._controller.activeSidebarViewChanged.connect(self._onSidebarViewsChanged)

        # register Qt list roles
        self.addRoleName(self.IdRole, "id")
        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.ActiveRole, "active")

    ##  Update the model when new views are added or another view is made the active view.
    def _onSidebarViewsChanged(self):
        items = []
        current_view_id = None

        sidebar_views = self._controller.getAllSidebarViews()
        current_view = self._controller.getActiveSidebarView()
        if current_view:
            current_view_id = current_view.getPluginId()

        for sidebar_view_id, sidebar_view in sidebar_views.items():

            # Override fields for default settings sidebar
            if sidebar_view_id == "default":
                items.append({
                    "id": "default",
                    "name": "Print settings",
                    "weight": 0,
                    "active": current_view_id == "default"
                })
                continue

            sidebar_view_metadata = PluginRegistry.getInstance().getMetaData(sidebar_view_id).get("sidebar_view", {})

            # Skip view modes that are marked as not visible
            if "visible" in sidebar_view_metadata and not sidebar_view_metadata["visible"]:
                continue

            name = sidebar_view_metadata.get("name", sidebar_view_id)
            weight = sidebar_view_metadata.get("weight", 0)

            items.append({
                "id": sidebar_view_id,
                "name": name,
                "active": sidebar_view_id == current_view_id,
                "weight": weight
            })

        # Sort the views by weight
        items.sort(key=lambda t: t["weight"])
        self.setItems(items)
