# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt

from UM.Application import Application
from UM.Qt.ListModel import ListModel
from UM.Util import parseBool


class NozzleModel(ListModel):
    IdRole = Qt.UserRole + 1
    HotendNameRole = Qt.UserRole + 2
    ContainerNodeRole = Qt.UserRole + 3

    def __init__(self, parent = None):
        super().__init__(parent)

        self.addRoleName(self.IdRole, "id")
        self.addRoleName(self.HotendNameRole, "hotend_name")
        self.addRoleName(self.ContainerNodeRole, "container_node")

        Application.getInstance().globalContainerStackChanged.connect(self._update)
        Application.getInstance().getMachineManager().activeVariantChanged.connect(self._update)
        Application.getInstance().getMachineManager().activeStackChanged.connect(self._update)
        Application.getInstance().getMachineManager().activeMaterialChanged.connect(self._update)

    def _update(self):
        self.items.clear()

        variant_manager = Application.getInstance()._variant_manager
        active_global_stack = Application.getInstance().getMachineManager()._global_container_stack
        if active_global_stack is None:
            self.setItems([])
            return

        has_variants = parseBool(active_global_stack.getMetaDataEntry("has_variants", False))
        if not has_variants:
            self.setItems([])
            return

        variant_node_dict = variant_manager.getVariantNodes(active_global_stack)
        if not variant_node_dict:
            self.setItems([])
            return

        item_list = []
        for hotend_name, container_node in sorted(variant_node_dict.items(), key = lambda i: i[0].upper()):
            item = {"id": hotend_name,
                    "hotend_name": hotend_name,
                    "container_node": container_node
                    }

            item_list.append(item)

        self.setItems(item_list)
