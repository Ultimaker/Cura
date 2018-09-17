# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any

from UM.Qt.ListModel import ListModel
from PyQt5.QtCore import pyqtSlot, Qt


class SidebarCustomMenuItemsModel(ListModel):
    name_role = Qt.UserRole + 1
    actions_role = Qt.UserRole + 2
    menu_item_role = Qt.UserRole + 3
    menu_item_icon_name_role = Qt.UserRole + 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self.addRoleName(self.name_role, "name")
        self.addRoleName(self.actions_role, "actions")
        self.addRoleName(self.menu_item_role, "menu_item")
        self.addRoleName(self.menu_item_icon_name_role, "icon_name")
        self._updateExtensionList()

    def _updateExtensionList(self)-> None:
        from cura.CuraApplication import CuraApplication
        for menu_item in CuraApplication.getInstance().getSidebarCustomMenuItems():

            self.appendItem({
                "name": menu_item["name"],
                "icon_name": menu_item["icon_name"],
                "actions": menu_item["actions"],
                "menu_item": menu_item["menu_item"]
            })

    @pyqtSlot(str, "QVariantList", "QVariantMap")
    def callMenuItemMethod(self, menu_item_name: str, menu_item_actions: list, kwargs: Any) -> None:
        for item in self._items:
            if menu_item_name == item["name"]:
                for method in menu_item_actions:
                    getattr(item["menu_item"], method)(kwargs)
                break