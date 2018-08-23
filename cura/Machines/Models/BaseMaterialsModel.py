# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt, pyqtSignal, pyqtProperty
from UM.Qt.ListModel import ListModel


## This is the base model class for GenericMaterialsModel and MaterialBrandsModel.
#  Those 2 models are used by the material drop down menu to show generic materials and branded materials separately.
#  The extruder position defined here is being used to bound a menu to the correct extruder. This is used in the top
#  bar menu "Settings" -> "Extruder nr" -> "Material" -> this menu
class BaseMaterialsModel(ListModel):

    extruderPositionChanged = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)

        from cura.CuraApplication import CuraApplication

        self._application = CuraApplication.getInstance()

        # Make these managers available to all material models
        self._extruder_manager = self._application.getExtruderManager()
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
        self.addRoleName(Qt.UserRole + 6, "material")
        self.addRoleName(Qt.UserRole + 7, "color_name")
        self.addRoleName(Qt.UserRole + 8, "color_code")
        self.addRoleName(Qt.UserRole + 9, "container_node")
        self.addRoleName(Qt.UserRole + 10, "is_favorite")

        self._extruder_position = 0
        self._extruder_stack = None

        self._available_materials = None
        self._favorite_ids = None

    def _updateExtruderStack(self):
        global_stack = self._machine_manager.activeMachine
        if global_stack is None:
            return

        if self._extruder_stack is not None:
            self._extruder_stack.pyqtContainersChanged.disconnect(self._update)
        self._extruder_stack = global_stack.extruders.get(str(self._extruder_position))
        if self._extruder_stack is not None:
            self._extruder_stack.pyqtContainersChanged.connect(self._update)
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

    ## This is an abstract method that needs to be implemented by the specific
    #  models themselves.
    def _update(self):
        pass

    ## This method is used by all material models in the beginning of the
    #  _update() method in order to prevent errors. It's the same in all models
    #  so it's placed here for easy access.
    def _canUpdate(self):
        global_stack = self._machine_manager.activeMachine

        if global_stack is None:
            return False

        extruder_position = str(self._extruder_position)

        if extruder_position not in global_stack.extruders:
            return False
        
        extruder_stack = global_stack.extruders[extruder_position]

        self._available_materials = self._material_manager.getAvailableMaterialsForMachineExtruder(global_stack, extruder_stack)
        if self._available_materials is None:
            return False

        return True

