# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QObject, pyqtSlot  # To allow the preference page proxy to be used from the actual preferences page.
from typing import TYPE_CHECKING

from cura.Settings.CuraContainerRegistry import CuraContainerRegistry  # To find the sets of materials belonging to each other, and currently loaded extruder stacks.

if TYPE_CHECKING:
    from cura.Machines.MaterialNode import MaterialNode

##  Proxy class to the materials page in the preferences.
#
#   This class handles the actions in that page, such as creating new materials,
#   renaming them, etc.
class MaterialManagementModel(QObject):
    ##  Can a certain material be deleted, or is it still in use in one of the
    #   container stacks anywhere?
    #
    #   We forbid the user from deleting a material if it's in use in any stack.
    #   Deleting it while it's in use can lead to corrupted stacks. In the
    #   future we might enable this functionality again (deleting the material
    #   from those stacks) but for now it is easier to prevent the user from
    #   doing this.
    #   \return Whether or not the material can be removed.
    @pyqtSlot("QVariant", result = bool)
    def canMaterialBeRemoved(self, material_node: "MaterialNode"):
        container_registry = CuraContainerRegistry.getInstance()
        ids_to_remove = {metadata.get("id", "") for metadata in container_registry.findInstanceContainersMetadata(base_file = material_node.base_file)}
        for extruder_stack in container_registry.findContainerStacks(type = "extruder_train"):
            if extruder_stack.material.getId() in ids_to_remove:
                return False
        return True