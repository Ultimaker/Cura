# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, List, Optional
from PyQt5.QtCore import Qt

from UM.Logger import Logger
from UM.Qt.ListModel import ListModel
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.Models.InstanceContainersModel import InstanceContainersModel


def getAvailableMaterials(extruder_position: Optional[int] = None):
    from cura.CuraApplication import CuraApplication
    machine_manager = CuraApplication.getInstance().getMachineManager()
    extruder_manager = CuraApplication.getInstance().getExtruderManager()

    material_manager = CuraApplication.getInstance()._material_manager

    active_global_stack = machine_manager._global_container_stack
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
    diameter = extruder_stack.getProperty("material_diameter", "value")

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

    def __init__(self, parent = None):
        super().__init__(parent)

        self.addRoleName(self.RootMaterialIdRole, "root_material_id")
        self.addRoleName(self.IdRole, "id")
        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.BrandRole, "brand")
        self.addRoleName(self.MaterialRole, "material")
        self.addRoleName(self.ColorRole, "color_name")
        self.addRoleName(self.ContainerNodeRole, "container_node")


class GenericMaterialsModel(BaseMaterialsModel):

    def __init__(self, parent = None):
        super().__init__(parent)

        from cura.CuraApplication import CuraApplication
        self._machine_manager = CuraApplication.getInstance().getMachineManager()
        self._extruder_manager = CuraApplication.getInstance().getExtruderManager()
        self._material_manager = CuraApplication.getInstance()._material_manager

        self._machine_manager.globalContainerChanged.connect(self._update)
        self._extruder_manager.activeExtruderChanged.connect(self._update)
        self._material_manager.materialsUpdated.connect(self._update)

        self._update()

    def _update(self):
        global_stack = self._machine_manager.activeMachine
        if global_stack is None:
            self.setItems([])
            return

        result_dict = getAvailableMaterials()
        if result_dict is None:
            self.setItems([])
            return

        item_list = []
        for root_material_id, container_node in result_dict.items():
            metadata = container_node.metadata
            # Only add results for generic materials
            if metadata["brand"].lower() != "generic":
                continue

            item = {"root_material_id": root_material_id,
                    "id": metadata["id"],
                    "name": metadata["name"],
                    "brand": metadata["brand"],
                    "material": metadata["material"],
                    "color_name": metadata["color_name"],
                    "container_node": container_node
                    }
            item_list.append(item)

        # Sort the item list by material name alphabetically
        item_list = sorted(item_list, key = lambda d: d["name"])

        self.setItems(item_list)


class MaterialsModelGroupedByType(ListModel):
    NameRole = Qt.UserRole + 1
    ColorsRole = Qt.UserRole + 2

    def __init__(self, parent = None):
        super().__init__(parent)

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.ColorsRole, "colors")


## Brand --> Material Type -> list of materials
class BrandMaterialsModel(ListModel):
    NameRole = Qt.UserRole + 1
    MaterialsRole = Qt.UserRole + 2

    def __init__(self, parent = None):
        super().__init__(parent)

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.MaterialsRole, "materials")

        from cura.CuraApplication import CuraApplication
        self._machine_manager = CuraApplication.getInstance().getMachineManager()
        extruder_manager = CuraApplication.getInstance().getExtruderManager()
        material_manager = CuraApplication.getInstance()._material_manager

        self._machine_manager.globalContainerChanged.connect(self._update)
        extruder_manager.activeExtruderChanged.connect(self._update)
        material_manager.materialsUpdated.connect(self._update)

    def _update(self):
        global_stack = self._machine_manager.activeMachine
        if global_stack is None:
            self.setItems([])
            return

        result_dict = getAvailableMaterials()
        if result_dict is None:
            self.setItems([])
            return

        brand_item_list = []
        brand_group_dict = {}
        for root_material_id, container_node in result_dict.items():
            metadata = container_node.metadata
            brand = metadata["brand"]
            # Only add results for generic materials
            if brand.lower() == "generic":
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
                    "container_node": container_node
                    }
            brand_group_dict[brand][material_type].append(item)

        for brand, material_dict in brand_group_dict.items():
            brand_item = {"name": brand,
                          "materials": MaterialsModelGroupedByType(self)}  # TODO

            material_type_item_list = []
            for material_type, material_list in material_dict.items():
                material_type_item = {"name": material_type,
                                      "colors": BaseMaterialsModel(self)}
                material_type_item["colors"].clear()
                material_type_item["colors"].setItems(material_list)

                material_type_item_list.append(material_type_item)

            brand_item["materials"].setItems(material_type_item_list)

            brand_item_list.append(brand_item)

        self.setItems(brand_item_list)


#
# This model is for the Material management page.
#
class MaterialsModel(ListModel):
    RootMaterialIdRole = Qt.UserRole + 1
    DisplayNameRole = Qt.UserRole + 2
    BrandRole = Qt.UserRole + 3
    MaterialTypeRole = Qt.UserRole + 4
    ColorNameRole = Qt.UserRole + 5
    ColorCodeRole = Qt.UserRole + 6
    ContainerNodeRole = Qt.UserRole + 7
    ContainerIdRole = Qt.UserRole + 8

    DescriptionRole = Qt.UserRole + 9
    AdhesionInfoRole = Qt.UserRole + 10
    ApproximateDiameterRole = Qt.UserRole + 11
    GuidRole = Qt.UserRole + 12
    DensityRole = Qt.UserRole + 13
    DiameterRole = Qt.UserRole + 14
    IsReadOnlyRole = Qt.UserRole + 15

    def __init__(self, parent = None):
        super().__init__(parent)

        self.addRoleName(self.RootMaterialIdRole, "root_material_id")
        self.addRoleName(self.DisplayNameRole, "name")
        self.addRoleName(self.BrandRole, "brand")
        self.addRoleName(self.MaterialTypeRole, "material")
        self.addRoleName(self.ColorNameRole, "color_name")
        self.addRoleName(self.ColorCodeRole, "color_code")
        self.addRoleName(self.ContainerNodeRole, "container_node")
        self.addRoleName(self.ContainerIdRole, "container_id")

        self.addRoleName(self.DescriptionRole, "description")
        self.addRoleName(self.AdhesionInfoRole, "adhesion_info")
        self.addRoleName(self.ApproximateDiameterRole, "approximate_diameter")
        self.addRoleName(self.GuidRole, "guid")
        self.addRoleName(self.DensityRole, "density")
        self.addRoleName(self.DiameterRole, "diameter")
        self.addRoleName(self.IsReadOnlyRole, "is_read_only")

        from cura.CuraApplication import CuraApplication
        self._container_registry = CuraApplication.getInstance().getContainerRegistry()
        self._machine_manager = CuraApplication.getInstance().getMachineManager()
        extruder_manager = CuraApplication.getInstance().getExtruderManager()
        material_manager = CuraApplication.getInstance()._material_manager

        self._machine_manager.globalContainerChanged.connect(self._update)
        extruder_manager.activeExtruderChanged.connect(self._update)
        material_manager.materialsUpdated.connect(self._update)

        self._update()

    def _update(self):
        global_stack = self._machine_manager.activeMachine
        if global_stack is None:
            self.setItems([])
            return

        result_dict = getAvailableMaterials()
        if result_dict is None:
            self.setItems([])
            return

        material_list = []
        for root_material_id, container_node in result_dict.items():
            keys_to_fetch = ("name",
                             "brand",
                             "material",
                             "color_name",
                             "color_code",
                             "description",
                             "adhesion_info",
                             "approximate_diameter",)

            item = {"root_material_id": container_node.metadata["base_file"],
                    "container_node": container_node,
                    "guid": container_node.metadata["GUID"],
                    "container_id": container_node.metadata["id"],
                    "density": container_node.metadata.get("properties", {}).get("density", ""),
                    "diameter": container_node.metadata.get("properties", {}).get("diameter", ""),
                    "is_read_only": self._container_registry.isReadOnly(container_node.metadata["id"]),
                    }

            for key in keys_to_fetch:
                item[key] = container_node.metadata.get(key, "")

            material_list.append(item)

        material_list = sorted(material_list, key = lambda k: (k["brand"], k["name"]))
        self.setItems(material_list)
