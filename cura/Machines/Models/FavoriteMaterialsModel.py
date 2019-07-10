# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from cura.Machines.Models.BaseMaterialsModel import BaseMaterialsModel

##  Model that shows the list of favorite materials.
class FavoriteMaterialsModel(BaseMaterialsModel):
    def __init__(self, parent = None):
        super().__init__(parent)
        self._update()

    def _update(self):
        if not self._canUpdate():
            return

        # Get updated list of favorites
        self._favorite_ids = self._material_manager.getFavorites()

        item_list = []

        for root_material_id, container_node in self._available_materials.items():
            metadata = container_node.getMetadata()

            # Do not include the materials from a to-be-removed package
            if bool(metadata.get("removed", False)):
                continue

            # Only add results for favorite materials
            if root_material_id not in self._favorite_ids:
                continue

            item = self._createMaterialItem(root_material_id, container_node)
            item_list.append(item)

        # Sort the item list alphabetically by name
        item_list = sorted(item_list, key = lambda d: d["brand"].upper())

        self.setItems(item_list)
