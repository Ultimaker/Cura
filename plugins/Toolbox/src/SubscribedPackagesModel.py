# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import re
from typing import Dict

from PyQt5.QtCore import Qt, pyqtProperty

from UM.Logger import Logger
from UM.Qt.ListModel import ListModel

from .ConfigsModel import ConfigsModel


from UM.PluginRegistry import PluginRegistry

##  Model that holds Cura packages. By setting the filter property the instances held by this model can be changed.
class SubscribedPackagesModel(ListModel):
    def __init__(self, parent = None):
        super().__init__(parent)


        self.addRoleName(Qt.UserRole + 1, "name")
        self.addRoleName(Qt.UserRole + 2, "icon_url")
        self.addRoleName(Qt.UserRole + 3, "is_compatible")

    def update(self):
        # items1 = []
        # items2 = []
        toolbox = PluginRegistry.getInstance().getPluginObject("Toolbox")
        # print("Compatible: {}".format(toolbox.subscribed_compatible_packages))
        # print("Incompatible: {}".format(toolbox.subscribed_incompatible_packages))

        # for incompatible in toolbox.subscribed_incompatible_packages:
        #     items1.append({
        #         "name": incompatible.package_id,
        #         "icon_url": incompatible.icon_url
        #     })
        #
        # for compatible in toolbox.subscribed_compatible_packages:
        #     items2.append({
        #         "name": compatible.package_id,
        #         "icon_url": compatible.icon_url
        #     })

        print("self.subscribed_packages: {}".format(toolbox.subscribed_packages))

        # final_list = items1 + items2
        self.setItems(toolbox.subscribed_packages)
        # self.setItems(final_list)
