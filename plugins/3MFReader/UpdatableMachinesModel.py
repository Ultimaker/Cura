# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Dict, List

from PyQt5.QtCore import Qt

from UM.Qt.ListModel import ListModel
from cura.Settings.GlobalStack import GlobalStack

create_new_list_item = {
    "id":   "new",
    "name": "Create new",
    "displayName": "Create new",
    "type": "default_option"  # to make sure we are not mixing the "Create new" option with a printer with id "new"
}  # type: Dict[str, str]


class UpdatableMachinesModel(ListModel):
    """Model that holds cura packages.

    By setting the filter property the instances held by this model can be changed.
    """

    def __init__(self, parent = None) -> None:
        super().__init__(parent)

        self.addRoleName(Qt.UserRole + 1, "id")
        self.addRoleName(Qt.UserRole + 2, "name")
        self.addRoleName(Qt.UserRole + 3, "displayName")
        self.addRoleName(Qt.UserRole + 4, "type")  # Either "default_option" or "machine"

    def update(self, machines: List[GlobalStack]) -> None:
        items = [create_new_list_item]  # type: List[Dict[str, str]]

        for machine in sorted(machines, key = lambda printer: printer.name):
            items.append({
                "id":   machine.id,
                "name": machine.name,
                "displayName": "Update " + machine.name,
                "type": "machine"
            })
        self.setItems(items)
