# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import copy  # To duplicate materials.
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot  # To allow the preference page proxy to be used from the actual preferences page.
from typing import Any, Dict, Optional, TYPE_CHECKING
import uuid  # To generate new GUIDs for new materials.

from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Signal import postponeSignals, CompressTechnique

import cura.CuraApplication  # Imported like this to prevent circular imports.
from cura.Machines.ContainerTree import ContainerTree
from cura.Settings.CuraContainerRegistry import CuraContainerRegistry  # To find the sets of materials belonging to each other, and currently loaded extruder stacks.

if TYPE_CHECKING:
    from cura.Machines.MaterialNode import MaterialNode

catalog = i18nCatalog("cura")

##  Proxy class to the materials page in the preferences.
#
#   This class handles the actions in that page, such as creating new materials,
#   renaming them, etc.
class MaterialManagementModel(QObject):
    ##  Triggered when a favorite is added or removed.
    #   \param The base file of the material is provided as parameter when this
    #   emits.
    favoritesChanged = pyqtSignal(str)

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
    def canMaterialBeRemoved(self, material_node: "MaterialNode") -> bool:
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

        # The material containers belonging to the same material file are supposed to work together. This postponeSignals()
        # does two things:
        #   - optimizing the signal emitting.
        #   - making sure that the signals will only be emitted after all the material containers have been removed.
        with postponeSignals(container_registry.containerRemoved, compress = CompressTechnique.CompressPerParameterValue):
            # CURA-6886: Some containers may not have been loaded. If remove one material container, its material file
            # will be removed. If later we remove a sub-material container which hasn't been loaded previously, it will
            # crash because removeContainer() requires to load the container first, but the material file was already
            # gone.
            for material_metadata in materials_this_base_file:
                container_registry.findInstanceContainers(id = material_metadata["id"])
            for material_metadata in materials_this_base_file:
                container_registry.removeContainer(material_metadata["id"])

    ##  Creates a duplicate of a material with the same GUID and base_file
    #   metadata.
    #   \param base_file: The base file of the material to duplicate.
    #   \param new_base_id A new material ID for the base material. The IDs of
    #   the submaterials will be based off this one. If not provided, a material
    #   ID will be generated automatically.
    #   \param new_metadata Metadata for the new material. If not provided, this
    #   will be duplicated from the original material.
    #   \return The root material ID of the duplicate material.
    def duplicateMaterialByBaseFile(self, base_file: str, new_base_id: Optional[str] = None,
                                    new_metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        container_registry = CuraContainerRegistry.getInstance()

        root_materials = container_registry.findContainers(id = base_file)
        if not root_materials:
            Logger.log("i", "Unable to duplicate the root material with ID {root_id}, because it doesn't exist.".format(root_id = base_file))
            return None
        root_material = root_materials[0]

        # Ensure that all settings are saved.
        application = cura.CuraApplication.CuraApplication.getInstance()
        application.saveSettings()

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
        for container_to_copy in container_registry.findInstanceContainers(base_file = base_file):
            if container_to_copy.getId() == base_file:
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

        # postpone the signals emitted when duplicating materials. This is easier on the event loop; changes the
        # behavior to be like a transaction. Prevents concurrency issues.
        with postponeSignals(container_registry.containerAdded, compress=CompressTechnique.CompressPerParameterValue):
            for container_to_add in new_containers:
                container_to_add.setDirty(True)
                container_registry.addContainer(container_to_add)

            # If the duplicated material was favorite then the new material should also be added to the favorites.
            favorites_set = set(application.getPreferences().getValue("cura/favorite_materials").split(";"))
            if base_file in favorites_set:
                favorites_set.add(new_base_id)
                application.getPreferences().setValue("cura/favorite_materials", ";".join(favorites_set))

        return new_base_id

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
    def duplicateMaterial(self, material_node: "MaterialNode", new_base_id: Optional[str] = None,
                          new_metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        return self.duplicateMaterialByBaseFile(material_node.base_file, new_base_id, new_metadata)

    ##  Create a new material by cloning the preferred material for the current
    #   material diameter and generate a new GUID.
    #
    #   The material type is explicitly left to be the one from the preferred
    #   material, since this allows the user to still have SOME profiles to work
    #   with.
    #   \return The ID of the newly created material.
    @pyqtSlot(result = str)
    def createMaterial(self) -> str:
        # Ensure all settings are saved.
        application = cura.CuraApplication.CuraApplication.getInstance()
        application.saveSettings()

        # Find the preferred material.
        extruder_stack = application.getMachineManager().activeStack
        active_variant_name = extruder_stack.variant.getName()
        approximate_diameter = int(extruder_stack.approximateMaterialDiameter)
        global_container_stack = application.getGlobalContainerStack()
        if not global_container_stack:
            return ""
        machine_node = ContainerTree.getInstance().machines[global_container_stack.definition.getId()]
        preferred_material_node = machine_node.variants[active_variant_name].preferredMaterial(approximate_diameter)

        # Create a new ID & new metadata for the new material.
        new_id = CuraContainerRegistry.getInstance().uniqueName("custom_material")
        new_metadata = {"name": catalog.i18nc("@label", "Custom Material"),
                        "brand": catalog.i18nc("@label", "Custom"),
                        "GUID": str(uuid.uuid4()),
                        }

        self.duplicateMaterial(preferred_material_node, new_base_id = new_id, new_metadata = new_metadata)
        return new_id

    ##  Adds a certain material to the favorite materials.
    #   \param material_base_file The base file of the material to add.
    @pyqtSlot(str)
    def addFavorite(self, material_base_file: str) -> None:
        application = cura.CuraApplication.CuraApplication.getInstance()
        favorites = application.getPreferences().getValue("cura/favorite_materials").split(";")
        if material_base_file not in favorites:
            favorites.append(material_base_file)
            application.getPreferences().setValue("cura/favorite_materials", ";".join(favorites))
            application.saveSettings()
            self.favoritesChanged.emit(material_base_file)

    ##  Removes a certain material from the favorite materials.
    #
    #   If the material was not in the favorite materials, nothing happens.
    @pyqtSlot(str)
    def removeFavorite(self, material_base_file: str) -> None:
        application = cura.CuraApplication.CuraApplication.getInstance()
        favorites = application.getPreferences().getValue("cura/favorite_materials").split(";")
        try:
            favorites.remove(material_base_file)
            application.getPreferences().setValue("cura/favorite_materials", ";".join(favorites))
            application.saveSettings()
            self.favoritesChanged.emit(material_base_file)
        except ValueError:  # Material was not in the favorites list.
            Logger.log("w", "Material {material_base_file} was already not a favorite material.".format(material_base_file = material_base_file))
