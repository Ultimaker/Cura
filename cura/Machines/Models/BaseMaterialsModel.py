# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional, Dict, Set

from PyQt5.QtCore import Qt, pyqtSignal, pyqtProperty
from UM.Qt.ListModel import ListModel


## This is the base model class for GenericMaterialsModel and MaterialBrandsModel.
#  Those 2 models are used by the material drop down menu to show generic materials and branded materials separately.
#  The extruder position defined here is being used to bound a menu to the correct extruder. This is used in the top
#  bar menu "Settings" -> "Extruder nr" -> "Material" -> this menu
from cura.Machines.MaterialNode import MaterialNode


class BaseMaterialsModel(ListModel):

    extruderPositionChanged = pyqtSignal()
    enabledChanged = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)
        from cura.CuraApplication import CuraApplication

        self._application = CuraApplication.getInstance()

        # Make these managers available to all material models
        self._container_registry = self._application.getInstance().getContainerRegistry()
        self._machine_manager = self._application.getMachineManager()
        self._material_manager = self._application.getMaterialManager()

        # Update the stack and the model data when the machine changes
        self._machine_manager.globalContainerChanged.connect(self._updateExtruderStack)

        # Update this model when switching machines
        self._machine_manager.activeStackChanged.connect(self._update)
        
        # Update this model when list of materials changes
        self._material_manager.materialsUpdated.connect(self._update)

        self.addRoleName(Qt.UserRole + 1, "root_material_id")
        self.addRoleName(Qt.UserRole + 2, "id")
        self.addRoleName(Qt.UserRole + 3, "GUID")
        self.addRoleName(Qt.UserRole + 4, "name")
        self.addRoleName(Qt.UserRole + 5, "brand")
        self.addRoleName(Qt.UserRole + 6, "description")
        self.addRoleName(Qt.UserRole + 7, "material")
        self.addRoleName(Qt.UserRole + 8, "color_name")
        self.addRoleName(Qt.UserRole + 9, "color_code")
        self.addRoleName(Qt.UserRole + 10, "density")
        self.addRoleName(Qt.UserRole + 11, "diameter")
        self.addRoleName(Qt.UserRole + 12, "approximate_diameter")
        self.addRoleName(Qt.UserRole + 13, "adhesion_info")
        self.addRoleName(Qt.UserRole + 14, "is_read_only")
        self.addRoleName(Qt.UserRole + 15, "container_node")
        self.addRoleName(Qt.UserRole + 16, "is_favorite")

        self._extruder_position = 0
        self._extruder_stack = None

        self._available_materials = None  # type: Optional[Dict[str, MaterialNode]]
        self._favorite_ids = set()  # type: Set[str]
        self._enabled = True

    def _updateExtruderStack(self):
        global_stack = self._machine_manager.activeMachine
        if global_stack is None:
            return

        if self._extruder_stack is not None:
            self._extruder_stack.pyqtContainersChanged.disconnect(self._update)
            self._extruder_stack.approximateMaterialDiameterChanged.disconnect(self._update)
        self._extruder_stack = global_stack.extruders.get(str(self._extruder_position))
        if self._extruder_stack is not None:
            self._extruder_stack.pyqtContainersChanged.connect(self._update)
            self._extruder_stack.approximateMaterialDiameterChanged.connect(self._update)
        # Force update the model when the extruder stack changes
        self._update()

    def setExtruderPosition(self, position: int):
        if self._extruder_stack is None or self._extruder_position != position:
            self._extruder_position = position
            self._updateExtruderStack()
            self.extruderPositionChanged.emit()

    @pyqtProperty(int, fset = setExtruderPosition, notify = extruderPositionChanged)
    def extruderPosition(self) -> int:
        return self._extruder_position

    def setEnabled(self, enabled):
        if self._enabled != enabled:
            self._enabled = enabled
            if self._enabled:
                # ensure the data is there again.
                self._update()
            self.enabledChanged.emit()

    @pyqtProperty(bool, fset=setEnabled, notify=enabledChanged)
    def enabled(self):
        return self._enabled

    ## This is an abstract method that needs to be implemented by the specific
    #  models themselves.
    def _update(self):
        pass

    ## This method is used by all material models in the beginning of the
    #  _update() method in order to prevent errors. It's the same in all models
    #  so it's placed here for easy access.
    def _canUpdate(self):
        global_stack = self._machine_manager.activeMachine

        if global_stack is None or not self._enabled:
            return False

        extruder_position = str(self._extruder_position)

        if extruder_position not in global_stack.extruders:
            return False
        
        extruder_stack = global_stack.extruders[extruder_position]
        self._available_materials = self._material_manager.getAvailableMaterialsForMachineExtruder(global_stack, extruder_stack)
        if self._available_materials is None:
            return False

        return True

    ## This is another convenience function which is shared by all material
    #  models so it's put here to avoid having so much duplicated code.
    def _createMaterialItem(self, root_material_id, container_node):
        metadata = container_node.getMetadata()
        item = {
            "root_material_id":     root_material_id,
            "id":                   metadata["id"],
            "container_id":         metadata["id"], # TODO: Remove duplicate in material manager qml
            "GUID":                 metadata["GUID"],
            "name":                 metadata["name"],
            "brand":                metadata["brand"],
            "description":          metadata["description"],
            "material":             metadata["material"],
            "color_name":           metadata["color_name"],
            "color_code":           metadata.get("color_code", ""),
            "density":              metadata.get("properties", {}).get("density", ""),
            "diameter":             metadata.get("properties", {}).get("diameter", ""),
            "approximate_diameter": metadata["approximate_diameter"],
            "adhesion_info":        metadata["adhesion_info"],
            "is_read_only":         self._container_registry.isReadOnly(metadata["id"]),
            "container_node":       container_node,
            "is_favorite":          root_material_id in self._favorite_ids
        }
        return item

