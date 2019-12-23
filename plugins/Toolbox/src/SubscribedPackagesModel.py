# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt

from UM.Qt.ListModel import ListModel
from UM.PluginRegistry import PluginRegistry

##  Model that holds Cura packages. By setting the filter property the instances held by this model can be changed.
class SubscribedPackagesModel(ListModel):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.addRoleName(Qt.UserRole + 1, "name")
        self.addRoleName(Qt.UserRole + 2, "icon_url")
        self.addRoleName(Qt.UserRole + 3, "is_compatible")

    def update(self):
        toolbox = PluginRegistry.getInstance().getPluginObject("Toolbox")
        self.setItems(toolbox.subscribed_packages)
