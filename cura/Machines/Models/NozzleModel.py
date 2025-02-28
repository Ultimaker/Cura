# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt6.QtCore import Qt

from UM.Logger import Logger
from UM.Qt.ListModel import ListModel
import cura.CuraApplication  # Imported like this to prevent circular dependencies.
from cura.Machines.ContainerTree import ContainerTree


class NozzleModel(ListModel):
    IdRole = Qt.ItemDataRole.UserRole + 1
    HotendNameRole = Qt.ItemDataRole.UserRole + 2
    ContainerNodeRole = Qt.ItemDataRole.UserRole + 3

    def __init__(self, parent=None):
        super().__init__(parent)

        self.addRoleName(self.IdRole, "id")
        self.addRoleName(self.HotendNameRole, "hotend_name")
        self.addRoleName(self.ContainerNodeRole, "container_node")

        cura.CuraApplication.CuraApplication.getInstance().getMachineManager().globalContainerChanged.connect(self._update)
        self._update()

    def _update(self):
        Logger.log("d", "Updating {model_class_name}.".format(model_class_name=self.__class__.__name__))

        global_stack = cura.CuraApplication.CuraApplication.getInstance().getGlobalContainerStack()
        if global_stack is None:
            self.setItems([])
            return
        machine_node = ContainerTree.getInstance().machines[global_stack.definition.getId()]

        if not machine_node.has_variants:
            self.setItems([])
            return

        item_list = []
        for hotend_name, container_node in sorted(machine_node.variants.items(), key=lambda i: i[0].upper()):
            item = {"id": hotend_name,
                    "hotend_name": hotend_name,
                    "container_node": container_node
                    }

            item_list.append(item)

        self.setItems(item_list)
