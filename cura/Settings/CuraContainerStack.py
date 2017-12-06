# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os.path

from typing import Any, Optional

from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject
from UM.FlameProfiler import pyqtSlot

from UM.Decorators import override
from UM.Logger import Logger
from UM.Settings.ContainerStack import ContainerStack, InvalidContainerStackError
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.Interfaces import ContainerInterface

from . import Exceptions


##  Base class for Cura related stacks that want to enforce certain containers are available.
#
#   This class makes sure that the stack has the following containers set: user changes, quality
#   changes, quality, material, variant, definition changes and finally definition. Initially,
#   these will be equal to the empty instance container.
#
#   The container types are determined based on the following criteria:
#   - user: An InstanceContainer with the metadata entry "type" set to "user".
#   - quality changes: An InstanceContainer with the metadata entry "type" set to "quality_changes".
#   - quality: An InstanceContainer with the metadata entry "type" set to "quality".
#   - material: An InstanceContainer with the metadata entry "type" set to "material".
#   - variant: An InstanceContainer with the metadata entry "type" set to "variant".
#   - definition changes: An InstanceContainer with the metadata entry "type" set to "definition_changes".
#   - definition: A DefinitionContainer.
#
#   Internally, this class ensures the mentioned containers are always there and kept in a specific order.
#   This also means that operations on the stack that modifies the container ordering is prohibited and
#   will raise an exception.
class CuraContainerStack(ContainerStack):
    def __init__(self, container_id: str, *args, **kwargs):
        super().__init__(container_id, *args, **kwargs)

        self._container_registry = ContainerRegistry.getInstance()

        self._empty_instance_container = self._container_registry.getEmptyInstanceContainer()

        self._empty_quality_changes = self._container_registry.findInstanceContainers(id = "empty_quality_changes")[0]
        self._empty_quality = self._container_registry.findInstanceContainers(id = "empty_quality")[0]
        self._empty_material = self._container_registry.findInstanceContainers(id = "empty_material")[0]
        self._empty_variant = self._container_registry.findInstanceContainers(id = "empty_variant")[0]

        self._containers = [self._empty_instance_container for i in range(len(_ContainerIndexes.IndexTypeMap))]
        self._containers[_ContainerIndexes.QualityChanges] = self._empty_quality_changes
        self._containers[_ContainerIndexes.Quality] = self._empty_quality
        self._containers[_ContainerIndexes.Material] = self._empty_material
        self._containers[_ContainerIndexes.Variant] = self._empty_variant

        self.containersChanged.connect(self._onContainersChanged)

        import cura.CuraApplication #Here to prevent circular imports.
        self.addMetaDataEntry("setting_version", cura.CuraApplication.CuraApplication.SettingVersion)

    # This is emitted whenever the containersChanged signal from the ContainerStack base class is emitted.
    pyqtContainersChanged = pyqtSignal()

    ##  Set the user changes container.
    #
    #   \param new_user_changes The new user changes container. It is expected to have a "type" metadata entry with the value "user".
    def setUserChanges(self, new_user_changes: InstanceContainer) -> None:
        self.replaceContainer(_ContainerIndexes.UserChanges, new_user_changes)

    ##  Get the user changes container.
    #
    #   \return The user changes container. Should always be a valid container, but can be equal to the empty InstanceContainer.
    @pyqtProperty(InstanceContainer, fset = setUserChanges, notify = pyqtContainersChanged)
    def userChanges(self) -> InstanceContainer:
        return self._containers[_ContainerIndexes.UserChanges]

    ##  Set the quality changes container.
    #
    #   \param new_quality_changes The new quality changes container. It is expected to have a "type" metadata entry with the value "quality_changes".
    def setQualityChanges(self, new_quality_changes: InstanceContainer, postpone_emit = False) -> None:
        self.replaceContainer(_ContainerIndexes.QualityChanges, new_quality_changes, postpone_emit = postpone_emit)

    ##  Set the quality changes container by an ID.
    #
    #   This will search for the specified container and set it. If no container was found, an error will be raised.
    #
    #   \param new_quality_changes_id The ID of the new quality changes container.
    #
    #   \throws Exceptions.InvalidContainerError Raised when no container could be found with the specified ID.
    def setQualityChangesById(self, new_quality_changes_id: str) -> None:
        quality_changes = ContainerRegistry.getInstance().findInstanceContainers(id = new_quality_changes_id)
        if quality_changes:
            self.setQualityChanges(quality_changes[0])
        else:
            raise Exceptions.InvalidContainerError("Could not find container with id {id}".format(id = new_quality_changes_id))

    ##  Get the quality changes container.
    #
    #   \return The quality changes container. Should always be a valid container, but can be equal to the empty InstanceContainer.
    @pyqtProperty(InstanceContainer, fset = setQualityChanges, notify = pyqtContainersChanged)
    def qualityChanges(self) -> InstanceContainer:
        return self._containers[_ContainerIndexes.QualityChanges]

    ##  Set the quality container.
    #
    #   \param new_quality The new quality container. It is expected to have a "type" metadata entry with the value "quality".
    def setQuality(self, new_quality: InstanceContainer, postpone_emit = False) -> None:
        self.replaceContainer(_ContainerIndexes.Quality, new_quality, postpone_emit = postpone_emit)

    ##  Set the quality container by an ID.
    #
    #   This will search for the specified container and set it. If no container was found, an error will be raised.
    #   There is a special value for ID, which is "default". The "default" value indicates the quality should be set
    #   to whatever the machine definition specifies as "preferred" container, or a fallback value. See findDefaultQuality
    #   for details.
    #
    #   \param new_quality_id The ID of the new quality container.
    #
    #   \throws Exceptions.InvalidContainerError Raised when no container could be found with the specified ID.
    def setQualityById(self, new_quality_id: str) -> None:
        quality = self._empty_quality
        if new_quality_id == "default":
            new_quality = self.findDefaultQuality()
            if new_quality:
                quality = new_quality
        else:
            qualities = ContainerRegistry.getInstance().findInstanceContainers(id = new_quality_id)
            if qualities:
                quality = qualities[0]
            else:
                raise Exceptions.InvalidContainerError("Could not find container with id {id}".format(id = new_quality_id))

        self.setQuality(quality)

    ##  Get the quality container.
    #
    #   \return The quality container. Should always be a valid container, but can be equal to the empty InstanceContainer.
    @pyqtProperty(InstanceContainer, fset = setQuality, notify = pyqtContainersChanged)
    def quality(self) -> InstanceContainer:
        return self._containers[_ContainerIndexes.Quality]

    ##  Set the material container.
    #
    #   \param new_quality_changes The new material container. It is expected to have a "type" metadata entry with the value "quality_changes".
    def setMaterial(self, new_material: InstanceContainer, postpone_emit = False) -> None:
        self.replaceContainer(_ContainerIndexes.Material, new_material, postpone_emit = postpone_emit)

    ##  Set the material container by an ID.
    #
    #   This will search for the specified container and set it. If no container was found, an error will be raised.
    #   There is a special value for ID, which is "default". The "default" value indicates the quality should be set
    #   to whatever the machine definition specifies as "preferred" container, or a fallback value. See findDefaultMaterial
    #   for details.
    #
    #   \param new_quality_changes_id The ID of the new material container.
    #
    #   \throws Exceptions.InvalidContainerError Raised when no container could be found with the specified ID.
    def setMaterialById(self, new_material_id: str) -> None:
        material = self._empty_material
        if new_material_id == "default":
            new_material = self.findDefaultMaterial()
            if new_material:
                material = new_material
        else:
            materials = ContainerRegistry.getInstance().findInstanceContainers(id = new_material_id)
            if materials:
                material = materials[0]
            else:
                raise Exceptions.InvalidContainerError("Could not find container with id {id}".format(id = new_material_id))

        self.setMaterial(material)

    ##  Get the material container.
    #
    #   \return The material container. Should always be a valid container, but can be equal to the empty InstanceContainer.
    @pyqtProperty(InstanceContainer, fset = setMaterial, notify = pyqtContainersChanged)
    def material(self) -> InstanceContainer:
        return self._containers[_ContainerIndexes.Material]

    ##  Set the variant container.
    #
    #   \param new_quality_changes The new variant container. It is expected to have a "type" metadata entry with the value "quality_changes".
    def setVariant(self, new_variant: InstanceContainer) -> None:
        self.replaceContainer(_ContainerIndexes.Variant, new_variant)

    ##  Set the variant container by an ID.
    #
    #   This will search for the specified container and set it. If no container was found, an error will be raised.
    #   There is a special value for ID, which is "default". The "default" value indicates the quality should be set
    #   to whatever the machine definition specifies as "preferred" container, or a fallback value. See findDefaultVariant
    #   for details.
    #
    #   \param new_quality_changes_id The ID of the new variant container.
    #
    #   \throws Exceptions.InvalidContainerError Raised when no container could be found with the specified ID.
    def setVariantById(self, new_variant_id: str) -> None:
        variant = self._empty_variant
        if new_variant_id == "default":
            new_variant = self.findDefaultVariant()
            if new_variant:
                variant = new_variant
        else:
            variants = ContainerRegistry.getInstance().findInstanceContainers(id = new_variant_id)
            if variants:
                variant = variants[0]
            else:
                raise Exceptions.InvalidContainerError("Could not find container with id {id}".format(id = new_variant_id))

        self.setVariant(variant)

    ##  Get the variant container.
    #
    #   \return The variant container. Should always be a valid container, but can be equal to the empty InstanceContainer.
    @pyqtProperty(InstanceContainer, fset = setVariant, notify = pyqtContainersChanged)
    def variant(self) -> InstanceContainer:
        return self._containers[_ContainerIndexes.Variant]

    ##  Set the definition changes container.
    #
    #   \param new_quality_changes The new definition changes container. It is expected to have a "type" metadata entry with the value "quality_changes".
    def setDefinitionChanges(self, new_definition_changes: InstanceContainer) -> None:
        self.replaceContainer(_ContainerIndexes.DefinitionChanges, new_definition_changes)

    ##  Set the definition changes container by an ID.
    #
    #   \param new_quality_changes_id The ID of the new definition changes container.
    #
    #   \throws Exceptions.InvalidContainerError Raised when no container could be found with the specified ID.
    def setDefinitionChangesById(self, new_definition_changes_id: str) -> None:
        new_definition_changes = ContainerRegistry.getInstance().findInstanceContainers(id = new_definition_changes_id)
        if new_definition_changes:
            self.setDefinitionChanges(new_definition_changes[0])
        else:
            raise Exceptions.InvalidContainerError("Could not find container with id {id}".format(id = new_definition_changes_id))

    ##  Get the definition changes container.
    #
    #   \return The definition changes container. Should always be a valid container, but can be equal to the empty InstanceContainer.
    @pyqtProperty(InstanceContainer, fset = setDefinitionChanges, notify = pyqtContainersChanged)
    def definitionChanges(self) -> InstanceContainer:
        return self._containers[_ContainerIndexes.DefinitionChanges]

    ##  Set the definition container.
    #
    #   \param new_quality_changes The new definition container. It is expected to have a "type" metadata entry with the value "quality_changes".
    def setDefinition(self, new_definition: DefinitionContainer) -> None:
        self.replaceContainer(_ContainerIndexes.Definition, new_definition)

    ##  Set the definition container by an ID.
    #
    #   \param new_quality_changes_id The ID of the new definition container.
    #
    #   \throws Exceptions.InvalidContainerError Raised when no container could be found with the specified ID.
    def setDefinitionById(self, new_definition_id: str) -> None:
        new_definition = ContainerRegistry.getInstance().findDefinitionContainers(id = new_definition_id)
        if new_definition:
            self.setDefinition(new_definition[0])
        else:
            raise Exceptions.InvalidContainerError("Could not find container with id {id}".format(id = new_definition_id))

    ##  Get the definition container.
    #
    #   \return The definition container. Should always be a valid container, but can be equal to the empty InstanceContainer.
    @pyqtProperty(QObject, fset = setDefinition, notify = pyqtContainersChanged)
    def definition(self) -> DefinitionContainer:
        return self._containers[_ContainerIndexes.Definition]

    @override(ContainerStack)
    def getBottom(self) -> "DefinitionContainer":
        return self.definition

    @override(ContainerStack)
    def getTop(self) -> "InstanceContainer":
        return self.userChanges

    ##  Check whether the specified setting has a 'user' value.
    #
    #   A user value here is defined as the setting having a value in either
    #   the UserChanges or QualityChanges container.
    #
    #   \return True if the setting has a user value, False if not.
    @pyqtSlot(str, result = bool)
    def hasUserValue(self, key: str) -> bool:
        if self._containers[_ContainerIndexes.UserChanges].hasProperty(key, "value"):
            return True

        if self._containers[_ContainerIndexes.QualityChanges].hasProperty(key, "value"):
            return True

        return False

    ##  Set a property of a setting.
    #
    #   This will set a property of a specified setting. Since the container stack does not contain
    #   any settings itself, it is required to specify a container to set the property on. The target
    #   container is matched by container type.
    #
    #   \param key The key of the setting to set.
    #   \param property_name The name of the property to set.
    #   \param new_value The new value to set the property to.
    #   \param target_container The type of the container to set the property of. Defaults to "user".
    def setProperty(self, key: str, property_name: str, new_value: Any, target_container: str = "user") -> None:
        container_index = _ContainerIndexes.TypeIndexMap.get(target_container, -1)
        if container_index != -1:
            self._containers[container_index].setProperty(key, property_name, new_value)
        else:
            raise IndexError("Invalid target container {type}".format(type = target_container))

    ##  Overridden from ContainerStack
    #
    #   Since we have a fixed order of containers in the stack and this method would modify the container
    #   ordering, we disallow this operation.
    @override(ContainerStack)
    def addContainer(self, container: ContainerInterface) -> None:
        raise Exceptions.InvalidOperationError("Cannot add a container to Global stack")

    ##  Overridden from ContainerStack
    #
    #   Since we have a fixed order of containers in the stack and this method would modify the container
    #   ordering, we disallow this operation.
    @override(ContainerStack)
    def insertContainer(self, index: int, container: ContainerInterface) -> None:
        raise Exceptions.InvalidOperationError("Cannot insert a container into Global stack")

    ##  Overridden from ContainerStack
    #
    #   Since we have a fixed order of containers in the stack and this method would modify the container
    #   ordering, we disallow this operation.
    @override(ContainerStack)
    def removeContainer(self, index: int = 0) -> None:
        raise Exceptions.InvalidOperationError("Cannot remove a container from Global stack")

    ##  Overridden from ContainerStack
    #
    #   Replaces the container at the specified index with another container.
    #   This version performs checks to make sure the new container has the expected metadata and type.
    #
    #   \throws Exception.InvalidContainerError Raised when trying to replace a container with a container that has an incorrect type.
    @override(ContainerStack)
    def replaceContainer(self, index: int, container: ContainerInterface, postpone_emit: bool = False) -> None:
        expected_type = _ContainerIndexes.IndexTypeMap[index]
        if expected_type == "definition":
            if not isinstance(container, DefinitionContainer):
                raise Exceptions.InvalidContainerError("Cannot replace container at index {index} with a container that is not a DefinitionContainer".format(index = index))
        elif container != self._empty_instance_container and container.getMetaDataEntry("type") != expected_type:
            raise Exceptions.InvalidContainerError("Cannot replace container at index {index} with a container that is not of {type} type, but {actual_type} type.".format(index = index, type = expected_type, actual_type = container.getMetaDataEntry("type")))

        super().replaceContainer(index, container, postpone_emit)

    ##  Overridden from ContainerStack
    #
    #   This deserialize will make sure the internal list of containers matches with what we expect.
    #   It will first check to see if the container at a certain index already matches with what we
    #   expect. If it does not, it will search for a matching container with the correct type. Should
    #   no container with the correct type be found, it will use the empty container.
    #
    #   \throws InvalidContainerStackError Raised when no definition can be found for the stack.
    @override(ContainerStack)
    def deserialize(self, contents: str, file_name: Optional[str] = None) -> None:
        super().deserialize(contents, file_name)

        new_containers = self._containers.copy()
        while len(new_containers) < len(_ContainerIndexes.IndexTypeMap):
            new_containers.append(self._empty_instance_container)

        # Validate and ensure the list of containers matches with what we expect
        for index, type_name in _ContainerIndexes.IndexTypeMap.items():
            try:
                container = new_containers[index]
            except IndexError:
                container = None

            if type_name == "definition":
                if not container or not isinstance(container, DefinitionContainer):
                    definition = self.findContainer(container_type = DefinitionContainer)
                    if not definition:
                        raise InvalidContainerStackError("Stack {id} does not have a definition!".format(id = self._id))

                    new_containers[index] = definition
                continue

            if not container or container.getMetaDataEntry("type") != type_name:
                actual_container = self.findContainer(type = type_name)
                if actual_container:
                    new_containers[index] = actual_container
                else:
                    new_containers[index] = self._empty_instance_container

        self._containers = new_containers

    ##  Find the variant that should be used as "default" variant.
    #
    #   This will search for variants that match the current definition and pick the preferred one,
    #   if specified by the machine definition.
    #
    #   The following criteria are used to find the default variant:
    #   - If the machine definition does not have a metadata entry "has_variants" set to True, return None
    #   - The definition of the variant should be the same as the machine definition for this stack.
    #   - The container should have a metadata entry "type" with value "variant".
    #   - If the machine definition has a metadata entry "preferred_variant", filter the variant IDs based on that.
    #
    #   \return The container that should be used as default, or None if nothing was found or the machine does not use variants.
    #
    #   \note This method assumes the stack has a valid machine definition.
    def findDefaultVariant(self) -> Optional[ContainerInterface]:
        definition = self._getMachineDefinition()
        # has_variants can be overridden in other containers and stacks.
        # In the case of UM2, it is overridden in the GlobalStack
        if not self.getMetaDataEntry("has_variants"):
            # If the machine does not use variants, we should never set a variant.
            return None

        # First add any variant. Later, overwrite with preference if the preference is valid.
        variant = None
        definition_id = self._findInstanceContainerDefinitionId(definition)
        variants = ContainerRegistry.getInstance().findInstanceContainers(definition = definition_id, type = "variant")
        if variants:
            variant = variants[0]

        preferred_variant_id = definition.getMetaDataEntry("preferred_variant")
        if preferred_variant_id:
            preferred_variants = ContainerRegistry.getInstance().findInstanceContainers(id = preferred_variant_id, definition = definition_id, type = "variant")
            if preferred_variants:
                variant = preferred_variants[0]
            else:
                Logger.log("w", "The preferred variant \"{variant}\" of stack {stack} does not exist or is not a variant.", variant = preferred_variant_id, stack = self.id)
                # And leave it at the default variant.

        if variant:
            return variant

        Logger.log("w", "Could not find a valid default variant for stack {stack}", stack = self.id)
        return None

    ##  Find the material that should be used as "default" material.
    #
    #   This will search for materials that match the current definition and pick the preferred one,
    #   if specified by the machine definition.
    #
    #   The following criteria are used to find the default material:
    #   - If the machine definition does not have a metadata entry "has_materials" set to True, return None
    #   - If the machine definition has a metadata entry "has_machine_materials", the definition of the material should
    #     be the same as the machine definition for this stack. Otherwise, the definition should be "fdmprinter".
    #   - The container should have a metadata entry "type" with value "material".
    #   - The material should have an approximate diameter that matches the machine
    #   - If the machine definition has a metadata entry "has_variants" and set to True, the "variant" metadata entry of
    #     the material should be the same as the ID of the variant in the stack. Only applies if "has_machine_materials" is also True.
    #   - If the stack currently has a material set, try to find a material that matches the current material by name.
    #   - Otherwise, if the machine definition has a metadata entry "preferred_material", try to find a material that matches the specified ID.
    #
    #   \return The container that should be used as default, or None if nothing was found or the machine does not use materials.
    def findDefaultMaterial(self) -> Optional[ContainerInterface]:
        definition = self._getMachineDefinition()
        if not definition.getMetaDataEntry("has_materials"):
            # Machine does not use materials, never try to set it.
            return None

        search_criteria = {"type": "material"}
        if definition.getMetaDataEntry("has_machine_materials"):
            search_criteria["definition"] = self._findInstanceContainerDefinitionId(definition)

            if definition.getMetaDataEntry("has_variants"):
                search_criteria["variant"] = self.variant.id
        else:
            search_criteria["definition"] = "fdmprinter"

        if self.material != self._empty_material:
            search_criteria["name"] = self.material.name
        else:
            preferred_material = definition.getMetaDataEntry("preferred_material")
            if preferred_material:
                search_criteria["id"] = preferred_material

        approximate_material_diameter = str(round(self.getProperty("material_diameter", "value")))
        search_criteria["approximate_diameter"] = approximate_material_diameter

        materials = ContainerRegistry.getInstance().findInstanceContainers(**search_criteria)
        if not materials:
            Logger.log("w", "The preferred material \"{material}\" could not be found for stack {stack}", material = preferred_material, stack = self.id)
            # We failed to find any materials matching the specified criteria, drop some specific criteria and try to find
            # a material that sort-of matches what we want.
            search_criteria.pop("variant", None)
            search_criteria.pop("id", None)
            search_criteria.pop("name", None)
            materials = ContainerRegistry.getInstance().findInstanceContainers(**search_criteria)

        if materials:
            return materials[0]

        Logger.log("w", "Could not find a valid material for stack {stack}", stack = self.id)
        return None

    ##  Find the quality that should be used as "default" quality.
    #
    #   This will search for qualities that match the current definition and pick the preferred one,
    #   if specified by the machine definition.
    #
    #   \return The container that should be used as default, or None if nothing was found.
    def findDefaultQuality(self) -> Optional[ContainerInterface]:
        definition = self._getMachineDefinition()
        registry = ContainerRegistry.getInstance()
        material_container = self.material if self.material != self._empty_instance_container else None

        search_criteria = {"type": "quality"}

        if definition.getMetaDataEntry("has_machine_quality"):
            search_criteria["definition"] = self._findInstanceContainerDefinitionId(definition)

            if definition.getMetaDataEntry("has_materials") and material_container:
                search_criteria["material"] = material_container.id
        else:
            search_criteria["definition"] = "fdmprinter"

        if self.quality != self._empty_quality:
            search_criteria["name"] = self.quality.name
        else:
            preferred_quality = definition.getMetaDataEntry("preferred_quality")
            if preferred_quality:
                search_criteria["id"] = preferred_quality

        containers = registry.findInstanceContainers(**search_criteria)
        if containers:
            return containers[0]

        if "material" in search_criteria:
            # First check if we can solve our material not found problem by checking if we can find quality containers
            # that are assigned to the parents of this material profile.
            try:
                inherited_files = material_container.getInheritedFiles()
            except AttributeError:  # Material_container does not support inheritance.
                inherited_files = []

            if inherited_files:
                for inherited_file in inherited_files:
                    # Extract the ID from the path we used to load the file.
                    search_criteria["material"] = os.path.basename(inherited_file).split(".")[0]
                    containers = registry.findInstanceContainers(**search_criteria)
                    if containers:
                        return containers[0]

            # We still weren't able to find a quality for this specific material.
            # Try to find qualities for a generic version of the material.
            material_search_criteria = {"type": "material", "material": material_container.getMetaDataEntry("material"), "color_name": "Generic"}
            if definition.getMetaDataEntry("has_machine_quality"):
                if self.material != self._empty_instance_container:
                    material_search_criteria["definition"] = material_container.getDefinition().id

                    if definition.getMetaDataEntry("has_variants"):
                        material_search_criteria["variant"] = material_container.getMetaDataEntry("variant")
                else:
                    material_search_criteria["definition"] = self._findInstanceContainerDefinitionId(definition)

                    if definition.getMetaDataEntry("has_variants") and self.variant != self._empty_instance_container:
                        material_search_criteria["variant"] = self.variant.id
            else:
                material_search_criteria["definition"] = "fdmprinter"
            material_containers = registry.findInstanceContainers(**material_search_criteria)
            # Try all materials to see if there is a quality profile available.
            for material_container in material_containers:
                search_criteria["material"] = material_container.getId()

                containers = registry.findInstanceContainers(**search_criteria)
                if containers:
                    return containers[0]

        if "name" in search_criteria or "id" in search_criteria:
            # If a quality by this name can not be found, try a wider set of search criteria
            search_criteria.pop("name", None)
            search_criteria.pop("id", None)

            containers = registry.findInstanceContainers(**search_criteria)
            if containers:
                return containers[0]

        return None

    ## protected:

    # Helper to make sure we emit a PyQt signal on container changes.
    def _onContainersChanged(self, container: Any) -> None:
        self.pyqtContainersChanged.emit()

    # Helper that can be overridden to get the "machine" definition, that is, the definition that defines the machine
    # and its properties rather than, for example, the extruder. Defaults to simply returning the definition property.
    def _getMachineDefinition(self) -> DefinitionContainer:
        return self.definition

    ##  Find the ID that should be used when searching for instance containers for a specified definition.
    #
    #   This handles the situation where the definition specifies we should use a different definition when
    #   searching for instance containers.
    #
    #   \param machine_definition The definition to find the "quality definition" for.
    #
    #   \return The ID of the definition container to use when searching for instance containers.
    @classmethod
    def _findInstanceContainerDefinitionId(cls, machine_definition: DefinitionContainer) -> str:
        quality_definition = machine_definition.getMetaDataEntry("quality_definition")
        if not quality_definition:
            return machine_definition.id

        definitions = ContainerRegistry.getInstance().findDefinitionContainers(id = quality_definition)
        if not definitions:
            Logger.log("w", "Unable to find parent definition {parent} for machine {machine}", parent = quality_definition, machine = machine_definition.id)
            return machine_definition.id

        return cls._findInstanceContainerDefinitionId(definitions[0])

## private:

# Private helper class to keep track of container positions and their types.
class _ContainerIndexes:
    UserChanges = 0
    QualityChanges = 1
    Quality = 2
    Material = 3
    Variant = 4
    DefinitionChanges = 5
    Definition = 6

    # Simple hash map to map from index to "type" metadata entry
    IndexTypeMap = {
        UserChanges: "user",
        QualityChanges: "quality_changes",
        Quality: "quality",
        Material: "material",
        Variant: "variant",
        DefinitionChanges: "definition_changes",
        Definition: "definition",
    }

    # Reverse lookup: type -> index
    TypeIndexMap = dict([(v, k) for k, v in IndexTypeMap.items()])
