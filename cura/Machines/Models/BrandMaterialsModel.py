# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt, pyqtSignal, pyqtProperty

from UM.Qt.ListModel import ListModel
from UM.Logger import Logger
from cura.Machines.Models.BaseMaterialsModel import BaseMaterialsModel


#
# This is an intermediate model to group materials with different colours for a same brand and type.
#
class MaterialsModelGroupedByType(ListModel):
    NameRole = Qt.UserRole + 1
    ColorsRole = Qt.UserRole + 2

    def __init__(self, parent = None):
        super().__init__(parent)

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.ColorsRole, "colors")


#
# This model is used to show branded materials in the material drop down menu.
# The structure of the menu looks like this:
#       Brand -> Material Type -> list of materials
#
# To illustrate, a branded material menu may look like this:
#      Ultimaker -> PLA -> Yellow PLA
#                       -> Black PLA
#                       -> ...
#                -> ABS -> White ABS
#                          ...
#
class BrandMaterialsModel(ListModel):
    NameRole = Qt.UserRole + 1
    MaterialsRole = Qt.UserRole + 2

    extruderPositionChanged = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.MaterialsRole, "materials")

        self._extruder_position = 0
        self._extruder_stack = None

        from cura.CuraApplication import CuraApplication
        self._machine_manager = CuraApplication.getInstance().getMachineManager()
        self._extruder_manager = CuraApplication.getInstance().getExtruderManager()
        self._material_manager = CuraApplication.getInstance().getMaterialManager()

        self._machine_manager.globalContainerChanged.connect(self._updateExtruderStack)
        self._machine_manager.activeStackChanged.connect(self._update) #Update when switching machines.
        self._material_manager.materialsUpdated.connect(self._update) #Update when the list of materials changes.
        self._update()

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

    @pyqtProperty(int, fset=setExtruderPosition, notify=extruderPositionChanged)
    def extruderPosition(self) -> int:
        return self._extruder_position

    def _update(self):
        Logger.log("d", "Updating {model_class_name}.".format(model_class_name = self.__class__.__name__))
        global_stack = self._machine_manager.activeMachine
        if global_stack is None:
            self.setItems([])
            return
        extruder_position = str(self._extruder_position)
        if extruder_position not in global_stack.extruders:
            self.setItems([])
            return
        extruder_stack = global_stack.extruders[str(self._extruder_position)]

        available_material_dict = self._material_manager.getAvailableMaterialsForMachineExtruder(global_stack,
                                                                                                 extruder_stack)
        if available_material_dict is None:
            self.setItems([])
            return

        brand_item_list = []
        brand_group_dict = {}
        for root_material_id, container_node in available_material_dict.items():
            metadata = container_node.metadata
            brand = metadata["brand"]
            # Only add results for generic materials
            if brand.lower() == "generic":
                continue
            if not metadata.get("compatible", True):
                continue

            if brand not in brand_group_dict:
                brand_group_dict[brand] = {}

            material_type = metadata["material"]
            if material_type not in brand_group_dict[brand]:
                brand_group_dict[brand][material_type] = []

            item = {"root_material_id": root_material_id,
                    "id": metadata["id"],
                    "name": metadata["name"],
                    "brand": metadata["brand"],
                    "material": metadata["material"],
                    "color_name": metadata["color_name"],
                    "container_node": container_node,
                    "compatible": metadata.get("compatible", True)
                    }
            brand_group_dict[brand][material_type].append(item)

        for brand, material_dict in brand_group_dict.items():
            brand_item = {"name": brand,
                          "materials": MaterialsModelGroupedByType(self)}

            material_type_item_list = []
            for material_type, material_list in material_dict.items():
                material_type_item = {"name": material_type,
                                      "colors": BaseMaterialsModel(self)}
                material_type_item["colors"].clear()

                # Sort materials by name
                material_list = sorted(material_list, key = lambda x: x["name"].upper())
                material_type_item["colors"].setItems(material_list)

                material_type_item_list.append(material_type_item)

            # Sort material type by name
            material_type_item_list = sorted(material_type_item_list, key = lambda x: x["name"].upper())
            brand_item["materials"].setItems(material_type_item_list)

            brand_item_list.append(brand_item)

        # Sort brand by name
        brand_item_list = sorted(brand_item_list, key = lambda x: x["name"].upper())
        self.setItems(brand_item_list)
