# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from dataclasses import asdict

from typing import cast, Dict, TYPE_CHECKING, Any

from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.SettingFunction import SettingFunction
from cura.Settings.GlobalStack import GlobalStack

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

    def getAllGlobalSettings(self) -> Dict[str, Any]:
        global_stack = cast(GlobalStack, self.application.getGlobalContainerStack())

        all_settings = {}
        for setting in global_stack.getAllKeys():
            all_settings[setting] = self._retrieveValue(global_stack, setting)

        return all_settings

    def getSliceMetadata(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Get all changed settings and all settings. For each extruder and the global stack"""
        print_information = self.application.getPrintInformation()
        machine_manager = self.application.getMachineManager()
        settings = {
            "material": {
                "length": print_information.materialLengths,
                "weight": print_information.materialWeights,
                "cost": print_information.materialCosts,
            },
            "global": {
                "changes": {},
                "all_settings": {},
            },
            "quality": asdict(machine_manager.activeQualityDisplayNameMap()),
        }

        global_stack = cast(GlobalStack, self.application.getGlobalContainerStack())

        # Add global user or quality changes
        global_flattened_changes = InstanceContainer.createMergedInstanceContainer(global_stack.userChanges, global_stack.qualityChanges)
        for setting in global_flattened_changes.getAllKeys():
            settings["global"]["changes"][setting] = self._retrieveValue(global_flattened_changes, setting)

        # Get global all settings values without user or quality changes
        for setting in global_stack.getAllKeys():
            settings["global"]["all_settings"][setting] = self._retrieveValue(global_stack, setting)

        for i, extruder in enumerate(global_stack.extruderList):
            # Add extruder fields to settings dictionary
            settings[f"extruder_{i}"] = {
                "changes": {},
                "all_settings": {},
            }

            # Add extruder user or quality changes
            extruder_flattened_changes = InstanceContainer.createMergedInstanceContainer(extruder.userChanges, extruder.qualityChanges)
            for setting in extruder_flattened_changes.getAllKeys():
                settings[f"extruder_{i}"]["changes"][setting] = self._retrieveValue(extruder_flattened_changes, setting)

            # Get extruder all settings values without user or quality changes
            for setting in extruder.getAllKeys():
                settings[f"extruder_{i}"]["all_settings"][setting] = self._retrieveValue(extruder, setting)

        return settings

    @staticmethod
    def _retrieveValue(container: InstanceContainer, setting_: str):
        value_ = container.getProperty(setting_, "value")
        for _ in range(0, 1024):  # Prevent possibly endless loop by not using a limit.
            if not isinstance(value_, SettingFunction):
                return value_  # Success!
            value_ = value_(container)
        return 0  # Fallback value after breaking possibly endless loop.