# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Logger import Logger
from cura.Machines.Models.BaseMaterialsModel import BaseMaterialsModel


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

    def _update(self) -> None:
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

        item_list = []
        for root_material_id, container_node in available_material_dict.items():
            metadata = container_node.metadata
            # Only add results for generic materials
            if metadata["brand"].lower() != "generic":
                continue
            if not metadata.get("compatible", True):
                continue

            item = {"root_material_id": root_material_id,
                    "id": metadata["id"],
                    "name": metadata["name"],
                    "brand": metadata["brand"],
                    "material": metadata["material"],
                    "color_name": metadata["color_name"],
                    "container_node": container_node,
                    "compatible": metadata.get("compatible", True)
                    }
            item_list.append(item)

        # Sort the item list by material name alphabetically
        item_list = sorted(item_list, key = lambda d: d["name"].upper())

        self.setItems(item_list)
