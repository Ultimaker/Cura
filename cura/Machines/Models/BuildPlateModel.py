# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt

from UM.Application import Application
from UM.Logger import Logger
from UM.Qt.ListModel import ListModel
from UM.Util import parseBool

from cura.Machines.VariantType import VariantType


class BuildPlateModel(ListModel):
    NameRole = Qt.UserRole + 1
    ContainerNodeRole = Qt.UserRole + 2

    def __init__(self, parent = None):
        super().__init__(parent)

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.ContainerNodeRole, "container_node")

        self._application = Application.getInstance()
        self._variant_manager = self._application._variant_manager
        self._machine_manager = self._application.getMachineManager()

        self._machine_manager.globalContainerChanged.connect(self._update)

        self._update()

    def _update(self):
        Logger.log("d", "Updating {model_class_name}.".format(model_class_name = self.__class__.__name__))
        global_stack = self._machine_manager._global_container_stack
        if not global_stack:
            self.setItems([])
            return

        has_variants = parseBool(global_stack.getMetaDataEntry("has_variant_buildplates", False))
        if not has_variants:
            self.setItems([])
            return

        variant_dict = self._variant_manager.getVariantNodes(global_stack, variant_type = VariantType.BUILD_PLATE)

        item_list = []
        for name, variant_node in variant_dict.items():
            item = {"name": name,
                    "container_node": variant_node}
            item_list.append(item)
        self.setItems(item_list)
