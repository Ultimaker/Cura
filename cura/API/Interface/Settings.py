# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication


class Settings:
    """The Interface.Settings API provides a version-proof bridge
     between Cura's
    
    (currently) sidebar UI and plug-ins that hook into it.
    
    Usage:

    .. code-block:: python

       from cura.API import CuraAPI
       api = CuraAPI()
       api.interface.settings.getContextMenuItems()
       data = {
       "name": "My Plugin Action",
       "iconName": "my-plugin-icon",
       "actions": my_menu_actions,
       "menu_item": MyPluginAction(self)
       }
       api.interface.settings.addContextMenuItem(data)
    """

    def __init__(self, application: "CuraApplication") -> None:
        self.application = application

    def addContextMenuItem(self, menu_item: dict) -> None:
        """Add items to the sidebar context menu.
        
        :param menu_item: dict containing the menu item to add.
        """

        self.application.addSidebarCustomMenuItem(menu_item)

    def getContextMenuItems(self) -> list:
        """Get all custom items currently added to the sidebar context menu.
        
        :return: List containing all custom context menu items.
        """

        return self.application.getSidebarCustomMenuItems()
