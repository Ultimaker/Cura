# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, List
from PyQt5.QtCore import Qt


from UM.Logger import Logger
from UM.Qt.ListModel import ListModel
from UM.Settings.ContainerRegistry import ContainerRegistry #To listen for changes to the materials.
from UM.Settings.Models.InstanceContainersModel import InstanceContainersModel #We're extending this class.


def getAvailableMaterials():
    from cura.CuraApplication import CuraApplication
    machine_manager = CuraApplication.getInstance().getMachineManager()
    extruder_manager = CuraApplication.getInstance().getExtruderManager()

    material_manager = CuraApplication.getInstance()._material_manager

    active_global_stack = machine_manager._global_container_stack
    active_extruder_stack = extruder_manager.getActiveExtruderStack()

    if active_global_stack is None or active_extruder_stack is None:
        Logger.log("d", "Active global stack [%s] or extruder stack [%s] is None, setting material list to empty.",
                   active_global_stack, active_extruder_stack)
        return

    machine_definition_id = active_global_stack.definition.getId()
    variant_name = None
    if active_extruder_stack.variant.getId() != "empty_variant":
        variant_name = active_extruder_stack.variant.getName()
    diameter = active_extruder_stack.getProperty("material_diameter", "value")

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
    ContainerNodeRole = Qt.UserRole + 6

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
        machine_manager = CuraApplication.getInstance().getMachineManager()
        extruder_manager = CuraApplication.getInstance().getExtruderManager()
        material_manager = CuraApplication.getInstance()._material_manager

        machine_manager.globalContainerChanged.connect(self._update)
        extruder_manager.activeExtruderChanged.connect(self._update)
        material_manager.materialsUpdated.connect(self._update)

    def _update(self):
        item_list = []
        result_dict = getAvailableMaterials()
        if result_dict is None:
            self.setItems([])
            return

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
        machine_manager = CuraApplication.getInstance().getMachineManager()
        extruder_manager = CuraApplication.getInstance().getExtruderManager()
        material_manager = CuraApplication.getInstance()._material_manager

        machine_manager.globalContainerChanged.connect(self._update)
        extruder_manager.activeExtruderChanged.connect(self._update)
        material_manager.materialsUpdated.connect(self._update)

    def _update(self):
        brand_item_list = []
        result_dict = getAvailableMaterials()
        if result_dict is None:
            self.setItems([])
            return

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


##  A model that shows a list of currently valid materials. Used by management page.
class MaterialsModel(InstanceContainersModel):
    def __init__(self, parent = None):
        super().__init__(parent)

        ContainerRegistry.getInstance().containerMetaDataChanged.connect(self._onContainerMetaDataChanged)

    ##  Called when the metadata of the container was changed.
    #
    #   This makes sure that we only update when it was a material that changed.
    #
    #   \param container The container whose metadata was changed.
    def _onContainerMetaDataChanged(self, container):
        if container.getMetaDataEntry("type") == "material": #Only need to update if a material was changed.
            self._container_change_timer.start()

    def _onContainerChanged(self, container):
        if container.getMetaDataEntry("type", "") == "material":
            super()._onContainerChanged(container)

    ##  Group brand together
    def _sortKey(self, item) -> List[Any]:
        result = []
        result.append(item["metadata"]["brand"])
        result.append(item["metadata"]["material"])
        result.append(item["metadata"]["name"])
        result.append(item["metadata"]["color_name"])
        result.append(item["metadata"]["id"])
        result.extend(super()._sortKey(item))
        return result
