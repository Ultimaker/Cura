# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication


##  The Interface.Settings API provides a version-proof bridge between Cura's
#   (currently) sidebar UI and plug-ins that hook into it.
#
#   Usage:
#       ``from cura.API import CuraAPI
#       api = CuraAPI()
#       api.interface.settings.getContextMenuItems()
#       data = {
#           "name": "My Plugin Action",
#           "iconName": "my-plugin-icon",
#           "actions": my_menu_actions,
#           "menu_item": MyPluginAction(self)
#       }
#       api.interface.settings.addContextMenuItem(data)``

class Settings:

    def __init__(self, application: "CuraApplication") -> None:
        self.application = application

    ##  Add items to the sidebar context menu.
    #   \param menu_item dict containing the menu item to add.
    def addContextMenuItem(self, menu_item: dict) -> None:
        self.application.addSidebarCustomMenuItem(menu_item)

    ##  Get all custom items currently added to the sidebar context menu.
    #   \return List containing all custom context menu items.
    def getContextMenuItems(self) -> list:
        return self.application.getSidebarCustomMenuItems()
