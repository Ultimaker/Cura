# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt, pyqtSignal, pyqtProperty

from UM.Qt.ListModel import ListModel


#
# This is the base model class for GenericMaterialsModel and BrandMaterialsModel
# Those 2 models are used by the material drop down menu to show generic materials and branded materials separately.
# The extruder position defined here is being used to bound a menu to the correct extruder. This is used in the top
# bar menu "Settings" -> "Extruder nr" -> "Material" -> this menu
#
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
