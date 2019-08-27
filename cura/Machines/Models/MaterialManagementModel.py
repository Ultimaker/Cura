# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import copy  # To duplicate materials.
from PyQt5.QtCore import QObject, pyqtSlot  # To allow the preference page proxy to be used from the actual preferences page.
from typing import Any, Dict, Optional, TYPE_CHECKING

from UM.Logger import Logger

import cura.CuraApplication  # Imported like this to prevent circular imports.
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

    ##  Creates a duplicate of a material with the same GUID and base_file
    #   metadata.
    #   \param material_node The node representing the material to duplicate.
    #   \param new_base_id A new material ID for the base material. The IDs of
    #   the submaterials will be based off this one. If not provided, a material
    #   ID will be generated automatically.
    #   \param new_metadata Metadata for the new material. If not provided, this
    #   will be duplicated from the original material.
    #   \return The root material ID of the duplicate material.
    @pyqtSlot("QVariant", result = str)
    def duplicateMaterial(self, material_node: "MaterialNode", new_base_id: Optional[str] = None, new_metadata: Dict[str, Any] = None) -> Optional[str]:
        container_registry = CuraContainerRegistry.getInstance()

        root_materials = container_registry.findContainers(id = material_node.base_file)
        if not root_materials:
            Logger.log("i", "Unable to duplicate the root material with ID {root_id}, because it doesn't exist.".format(root_id = material_node.base_file))
            return None
        root_material = root_materials[0]

        # Ensure that all settings are saved.
        cura.CuraApplication.CuraApplication.getInstance().saveSettings()

        # Create a new ID and container to hold the data.
        if new_base_id is None:
            new_base_id = container_registry.uniqueName(root_material.getId())
        new_root_material = copy.deepcopy(root_material)
        new_root_material.getMetaData()["id"] = new_base_id
        new_root_material.getMetaData()["base_file"] = new_base_id
        if new_metadata is not None:
            new_root_material.getMetaData().update(new_metadata)
        new_containers = [new_root_material]

        # Clone all submaterials.
        for container_to_copy in container_registry.findInstanceContainers(base_file = material_node.base_file):
            if container_to_copy.getId() == material_node.base_file:
                continue  # We already have that one. Skip it.
            new_id = new_base_id
            definition = container_to_copy.getMetaDataEntry("definition")
            if definition != "fdmprinter":
                new_id += "_" + definition
                variant_name = container_to_copy.getMetaDataEntry("variant_name")
                if variant_name:
                    new_id += "_" + variant_name.replace(" ", "_")

            new_container = copy.deepcopy(container_to_copy)
            new_container.getMetaData()["id"] = new_id
            new_container.getMetaData()["base_file"] = new_base_id
            if new_metadata is not None:
                new_container.getMetaData().update(new_metadata)
            new_containers.append(new_container)

        for container_to_add in new_containers:
            container_to_add.setDirty(True)
            container_registry.addContainer(container_to_add)

        # If the duplicated material was favorite then the new material should also be added to the favorites.
        # TODO: Move favourites to here.
        #if material_node.base_file in self.getFavorites():
        #    self.addFavorite(new_base_id)

        return new_base_id