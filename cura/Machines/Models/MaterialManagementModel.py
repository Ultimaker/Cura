# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QObject, pyqtSlot  # To allow the preference page proxy to be used from the actual preferences page.
from typing import TYPE_CHECKING

from UM.Logger import Logger

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
    #   \param material_node The ContainerTree node of the material to check.
    #   \return Whether or not the material can be removed.
    @pyqtSlot("QVariant", result = bool)
    def canMaterialBeRemoved(self, material_node: "MaterialNode"):
        container_registry = CuraContainerRegistry.getInstance()
        ids_to_remove = {metadata.get("id", "") for metadata in container_registry.findInstanceContainersMetadata(base_file = material_node.base_file)}
        for extruder_stack in container_registry.findContainerStacks(type = "extruder_train"):
            if extruder_stack.material.getId() in ids_to_remove:
                return False
        return True

    ##  Change the user-visible name of a material.
    #   \param material_node The ContainerTree node of the material to rename.
    #   \param name The new name for the material.
    @pyqtSlot("QVariant", str)
    def setMaterialName(self, material_node: "MaterialNode", name: str) -> None:
        container_registry = CuraContainerRegistry.getInstance()
        root_material_id = material_node.base_file
        if container_registry.isReadOnly(root_material_id):
            Logger.log("w", "Cannot set name of read-only container %s.", root_material_id)
            return
        return container_registry.findContainers(id = root_material_id)[0].setName(name)

    ##  Deletes a material from Cura.
    #
    #   This function does not do any safety checking any more. Please call this
    #   function only if:
    #   - The material is not read-only.
    #   - The material is not used in any stacks.
    #   If the material was not lazy-loaded yet, this will fully load the
    #   container. When removing this material node, all other materials with
    #   the same base fill will also be removed.
    #   \param material_node The material to remove.
    @pyqtSlot("QVariant")
    def removeMaterial(self, material_node: "MaterialNode") -> None:
        container_registry = CuraContainerRegistry.getInstance()
        materials_this_base_file = container_registry.findContainersMetadata(base_file = material_node.base_file)
        for material_metadata in materials_this_base_file:
            container_registry.removeContainer(material_metadata["id"])