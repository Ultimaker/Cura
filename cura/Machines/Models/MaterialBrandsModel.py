# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt, pyqtSignal
from UM.Qt.ListModel import ListModel
from cura.Machines.Models.BaseMaterialsModel import BaseMaterialsModel

class MaterialTypesModel(ListModel):

    def __init__(self, parent = None):
        super().__init__(parent)

        self.addRoleName(Qt.UserRole + 1, "name")
        self.addRoleName(Qt.UserRole + 2, "brand")
        self.addRoleName(Qt.UserRole + 3, "colors")

class MaterialBrandsModel(BaseMaterialsModel):

    extruderPositionChanged = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)

        self.addRoleName(Qt.UserRole + 1, "name")
        self.addRoleName(Qt.UserRole + 2, "material_types")

        self._update()

    def _update(self):
        if not self._canUpdate():
            return
        super()._update()

        brand_item_list = []
        brand_group_dict = {}

        # Part 1: Generate the entire tree of brands -> material types -> specific materials
        for root_material_id, container_node in self._available_materials.items():
            # Do not include the materials from a to-be-removed package
            if bool(container_node.getMetaDataEntry("removed", False)):
                continue

            # Add brands we haven't seen yet to the dict, skipping generics
            brand = container_node.getMetaDataEntry("brand", "")
            if brand.lower() == "generic":
                continue
            if brand not in brand_group_dict:
                brand_group_dict[brand] = {}

            # Add material types we haven't seen yet to the dict
            material_type = container_node.getMetaDataEntry("material", "")
            if material_type not in brand_group_dict[brand]:
                brand_group_dict[brand][material_type] = []

            # Now handle the individual materials
            item = self._createMaterialItem(root_material_id, container_node)
            if item:
                brand_group_dict[brand][material_type].append(item)

        # Part 2: Organize the tree into models
        #
        # Normally, the structure of the menu looks like this:
        #     Brand -> Material Type -> Specific Material
        #
        # To illustrate, a branded material menu may look like this:
        #     Ultimaker ┳ PLA ┳ Yellow PLA
        #               ┃     ┣ Black PLA
        #               ┃     ┗ ...
        #               ┃
        #               ┗ ABS ┳ White ABS
        #                     ┗ ...
        for brand, material_dict in brand_group_dict.items():

            material_type_item_list = []
            brand_item = {
                "name": brand,
                "material_types": MaterialTypesModel(self)
            }

            for material_type, material_list in material_dict.items():
                material_type_item = {
                    "name": material_type,
                    "brand": brand,
                    "colors": BaseMaterialsModel(self)
                }
                material_type_item["colors"].clear()

                # Sort materials by name
                material_list = sorted(material_list, key = lambda x: x["name"].upper())
                material_type_item["colors"].setItems(material_list)

                material_type_item_list.append(material_type_item)

            # Sort material type by name
            material_type_item_list = sorted(material_type_item_list, key = lambda x: x["name"].upper())
            brand_item["material_types"].setItems(material_type_item_list)

            brand_item_list.append(brand_item)

        # Sort brand by name
        brand_item_list = sorted(brand_item_list, key = lambda x: x["name"].upper())
        self.setItems(brand_item_list)
