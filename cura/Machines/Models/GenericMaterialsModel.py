# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from cura.Machines.Models.BaseMaterialsModel import BaseMaterialsModel

class GenericMaterialsModel(BaseMaterialsModel):

    def __init__(self, parent = None):
        super().__init__(parent)
        self._onChanged()

    def _update(self):
        if not self._canUpdate():
            return
        super()._update()

        item_list = []

        for root_material_id, container_node in self._available_materials.items():
            # Do not include the materials from a to-be-removed package
            if bool(container_node.getMetaDataEntry("removed", False)):
                continue

            # Only add results for generic materials
            if container_node.getMetaDataEntry("brand", "unknown").lower() != "generic":
                continue

            item = self._createMaterialItem(root_material_id, container_node)
            if item:
                item_list.append(item)

        # Sort the item list alphabetically by name
        item_list = sorted(item_list, key = lambda d: d["name"].upper())

        self.setItems(item_list)
