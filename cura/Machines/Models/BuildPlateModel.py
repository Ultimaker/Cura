# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt
from UM.Logger import Logger
from UM.Qt.ListModel import ListModel


class BuildPlateModel(ListModel):
    NameRole = Qt.UserRole + 1
    ContainerNodeRole = Qt.UserRole + 2

    def __init__(self, parent = None):
        super().__init__(parent)

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.ContainerNodeRole, "container_node")

        self._update()

    def _update(self):
        Logger.log("d", "Updating {model_class_name}.".format(model_class_name = self.__class__.__name__))
        self.setItems([])
        return
