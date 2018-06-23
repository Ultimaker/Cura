from UM.Qt.ListModel import ListModel
from PyQt5.QtCore import pyqtSlot, Qt

class SidebarCustomMenuItemsModel(ListModel):
    NameRole = Qt.UserRole + 1
    ActionsRole = Qt.UserRole + 2
    MenuItemRole = Qt.UserRole + 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.ActionsRole, "actions")
        self.addRoleName(self.MenuItemRole, "menu_item")
        self._updateExtensionList()

    def _updateExtensionList(self)-> None:
        from cura.CuraApplication import CuraApplication
        for menu_item in CuraApplication.getInstance().getSidebarCustomMenuItems():

            self.appendItem({
                    "name": menu_item["name"],
                    "actions": menu_item["actions"],
                    "menu_item": menu_item["menu_item"]
                })

    @pyqtSlot(str, "QVariantList")
    def callMenuItemMethod(self, menu_item_name: str, menu_item_actions: list)-> None:
        for item in self._items:
            if menu_item_name == item["name"]:
                for method in menu_item_actions:
                    getattr(item["menu_item"], method)()
                break