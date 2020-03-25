# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt

from UM.Qt.ListModel import ListModel


##  Model that holds supported configurations (for material/quality packages).
class ConfigsModel(ListModel):
    def __init__(self, parent = None):
        super().__init__(parent)

        self._configs = None

        self.addRoleName(Qt.UserRole + 1, "machine")
        self.addRoleName(Qt.UserRole + 2, "print_core")
        self.addRoleName(Qt.UserRole + 3, "build_plate")
        self.addRoleName(Qt.UserRole + 4, "support_material")
        self.addRoleName(Qt.UserRole + 5, "quality")

    def setConfigs(self, configs):
        self._configs = configs
        self._update()

    def _update(self):
        items = []
        for item in self._configs:
            items.append({
                "machine":          item["machine"],
                "print_core":       item["print_core"],
                "build_plate":      item["build_plate"],
                "support_material": item["support_material"],
                "quality":          item["quality"]
            })

        self.setItems(items)
