# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional
from PyQt5.QtCore import Qt, pyqtSignal, pyqtProperty

from UM.Logger import Logger
from UM.Qt.ListModel import ListModel


def getAvailableMaterials(extruder_position: Optional[int] = None):
    from cura.CuraApplication import CuraApplication
    machine_manager = CuraApplication.getInstance().getMachineManager()
    extruder_manager = CuraApplication.getInstance().getExtruderManager()
    material_manager = CuraApplication.getInstance().getMaterialManager()

    active_global_stack = machine_manager.activeMachine
    extruder_stack = extruder_manager.getActiveExtruderStack()
    if extruder_position is not None:
        if active_global_stack is not None:
            extruder_stack = active_global_stack.extruders.get(str(extruder_position))

    if active_global_stack is None or extruder_stack is None:
        Logger.log("d", "Active global stack [%s] or extruder stack [%s] is None, setting material list to empty.",
                   active_global_stack, extruder_stack)
        return

    machine_definition_id = active_global_stack.definition.getId()
    variant_name = None
    if extruder_stack.variant.getId() != "empty_variant":
        variant_name = extruder_stack.variant.getName()
    diameter = extruder_stack.approximateMaterialDiameter

    # Fetch the available materials (ContainerNode) for the current active machine and extruder setup.
    result_dict = material_manager.getAvailableMaterials(machine_definition_id, variant_name, diameter)
    return result_dict


class BaseMaterialsModel(ListModel):
    RootMaterialIdRole = Qt.UserRole + 1
    IdRole = Qt.UserRole + 2
    NameRole = Qt.UserRole + 3
    BrandRole = Qt.UserRole + 4
    MaterialRole = Qt.UserRole + 5
    ColorRole = Qt.UserRole + 6
    ContainerNodeRole = Qt.UserRole + 7

    extruderPositionChanged = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)

        self.addRoleName(self.RootMaterialIdRole, "root_material_id")
        self.addRoleName(self.IdRole, "id")
        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.BrandRole, "brand")
        self.addRoleName(self.MaterialRole, "material")
        self.addRoleName(self.ColorRole, "color_name")
        self.addRoleName(self.ContainerNodeRole, "container_node")

        self._extruder_position = 0

    def setExtruderPosition(self, position: int):
        if self._extruder_position != position:
            self._extruder_position = position
            self.extruderPositionChanged.emit()

    @pyqtProperty(int, fset = setExtruderPosition, notify = extruderPositionChanged)
    def extruderPosition(self) -> int:
        return self._extruder_positoin
