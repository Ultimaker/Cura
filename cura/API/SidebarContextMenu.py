# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from cura.CuraApplication import CuraApplication

##  The back-ups API provides a version-proof bridge between Cura's
#   Sidebar Context Menu and plug-ins that hook into it.
#
#   Usage:
#       ``from cura.API import CuraAPI
#       api = CuraAPI()
#       api.sidebar_context_menu.getSidebarMenuItems()
#       menu_actions = []
#       menu_actions.append("sidebarMenuItemOnClickHander")
#       data = {
#           "name": "My Plugin Action",
#           "iconName": "my-plugin-icon",
#           "actions": menu_actions,
#           "menu_item": MyPluginAction(self)
#       }
#       api.sidebar_context_menu.addSidebarMenuItems([])``
class SidebarContextMenu:

    _application = CuraApplication.getInstance()  # type: CuraApplication

    ##  Add items to the sidebar context menu.
    #   \param menu_item dict containing the menu item to add.
    def addSidebarMenuItem(self, menu_items: dict) -> None:
        self._application.addSidebarCustomMenuItem(menu_items)

    ##  Get all custom items currently added to the sidebar context menu.
    #   \return List containing all custom context menu items.
    def getSidebarMenuItems(self) -> list:
        return self._application.getSidebarCustomMenuItems()