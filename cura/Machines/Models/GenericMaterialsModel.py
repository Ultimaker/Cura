# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Dict
from UM.Logger import Logger
from cura.Machines.Models.BaseMaterialsModel import BaseMaterialsModel
from cura.Machines.MaterialNode import MaterialNode


class GenericMaterialsModel(BaseMaterialsModel):

    def __init__(self, parent = None):
        super().__init__(parent)

        from cura.CuraApplication import CuraApplication
        self._machine_manager = CuraApplication.getInstance().getMachineManager()
        self._extruder_manager = CuraApplication.getInstance().getExtruderManager()
        self._material_manager = CuraApplication.getInstance().getMaterialManager()

        self._machine_manager.activeStackChanged.connect(self._update) #Update when switching machines.
        self._material_manager.materialsUpdated.connect(self._update) #Update when the list of materials changes.
        self._update()

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
        extruder_stack = global_stack.extruders[extruder_position]

        available_material_dict = self._material_manager.getAvailableMaterialsForMachineExtruder(global_stack,
                                                                                                 extruder_stack)
        if available_material_dict is None:
            self.setItems([])
            return

        # Check if it's an Ultimaker printer
        printer_manufacturer = global_stack.getMetaDataEntry("manufacturer", "")
        is_ultimaker_printer = "ultimaker" in printer_manufacturer.lower()

        # For Ultimaker printers, only show the generic materials that are supported.
        if not is_ultimaker_printer:
            item_list = self._getGenericProfiles(available_material_dict)
        else:
            item_list = self._getUltimakerGenericProfiles(available_material_dict)

        # Sort the item list by material name alphabetically
        item_list = sorted(item_list, key = lambda d: d["name"].upper())

        self.setItems(item_list)

    def _getGenericProfiles(self, available_material_dict):
        item_list = []
        for root_material_id, container_node in available_material_dict.items():
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

        return item_list

    ## The method filters available materials by name. If material is not defined for Ultimaker printers
    #  then it will be removed
    #  \available_material_dict \type{dictionary}
    #  \return The filtered list
    def _getUltimakerGenericProfiles(self, available_material_dict: Dict[str, MaterialNode]):
        generic_item_list = []
        ultimaker_item_set = set()

        for root_material_id, container_node in available_material_dict.items():
            metadata = container_node.metadata

            is_ultimaker_brand = False
            brand_name = metadata["brand"].lower()

            if brand_name != "generic":
                if brand_name == 'ultimaker':
                    is_ultimaker_brand = True
                else:
                    continue

            item = {"root_material_id": root_material_id,
                    "id": metadata["id"],
                    "name": metadata["name"],
                    "brand": metadata["brand"],
                    "material": metadata["material"],
                    "color_name": metadata["color_name"],
                    "container_node": container_node
                    }
            if is_ultimaker_brand:
                ultimaker_item_set.add(item['material'])
            else:
                generic_item_list.append(item)

        # If material is not in ultimaker list then remove it
        item_list = [material for material in generic_item_list if material['material'] in ultimaker_item_set]

        return item_list
