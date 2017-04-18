# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from typing import Any

from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal

from UM.Decorators import override

from UM.MimeTypeDatabase import MimeType, MimeTypeDatabase
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

        self._empty_instance_container = ContainerRegistry.getInstance().getEmptyInstanceContainer()

        self._containers = [self._empty_instance_container for i in range(len(_ContainerIndexes.IndexTypeMap))]

        self.containersChanged.connect(self._onContainersChanged)

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
    def setQualityChanges(self, new_quality_changes: InstanceContainer) -> None:
        self.replaceContainer(_ContainerIndexes.QualityChanges, new_quality_changes)

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
    def setQuality(self, new_quality: InstanceContainer) -> None:
        self.replaceContainer(_ContainerIndexes.Quality, new_quality)

    ##  Set the quality container by an ID.
    #
    #   \param new_quality_id The ID of the new quality container.
    #
    #   \throws Exceptions.InvalidContainerError Raised when no container could be found with the specified ID.
    def setQualityById(self, new_quality_id: str) -> None:
        quality = ContainerRegistry.getInstance().findInstanceContainers(id = new_quality_id)
        if quality:
            self.setQuality(quality[0])
        else:
            raise Exceptions.InvalidContainerError("Could not find container with id {id}".format(id = new_quality_id))

    ##  Get the quality container.
    #
    #   \return The quality container. Should always be a valid container, but can be equal to the empty InstanceContainer.
    @pyqtProperty(InstanceContainer, fset = setQuality, notify = pyqtContainersChanged)
    def quality(self) -> InstanceContainer:
        return self._containers[_ContainerIndexes.Quality]

    ##  Set the material container.
    #
    #   \param new_quality_changes The new material container. It is expected to have a "type" metadata entry with the value "quality_changes".
    def setMaterial(self, new_material: InstanceContainer) -> None:
        self.replaceContainer(_ContainerIndexes.Material, new_material)

    ##  Set the material container by an ID.
    #
    #   \param new_quality_changes_id The ID of the new material container.
    #
    #   \throws Exceptions.InvalidContainerError Raised when no container could be found with the specified ID.
    def setMaterialById(self, new_material_id: str) -> None:
        material = ContainerRegistry.getInstance().findInstanceContainers(id = new_material_id)
        if material:
            self.setMaterial(material[0])
        else:
            raise Exceptions.InvalidContainerError("Could not find container with id {id}".format(id = new_material_id))

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
    #   \param new_quality_changes_id The ID of the new variant container.
    #
    #   \throws Exceptions.InvalidContainerError Raised when no container could be found with the specified ID.
    def setVariantById(self, new_variant_id: str) -> None:
        variant = ContainerRegistry.getInstance().findInstanceContainers(id = new_variant_id)
        if variant:
            self.setVariant(variant[0])
        else:
            raise Exceptions.InvalidContainerError("Could not find container with id {id}".format(id = new_variant_id))


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
    @pyqtProperty(DefinitionContainer, fset = setDefinition, notify = pyqtContainersChanged)
    def definition(self) -> DefinitionContainer:
        return self._containers[_ContainerIndexes.Definition]

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
        container_index = _ContainerIndexes.indexForType(target_container)
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
    def removeContainer(self, index: int) -> None:
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
    def deserialize(self, contents: str) -> None:
        super().deserialize(contents)

        new_containers = self._containers.copy()
        while(len(new_containers) < len(_ContainerIndexes.IndexTypeMap)):
            new_containers.append(self._empty_instance_container)

        # Validate and ensure the list of containers matches with what we expect
        for index, type_name in _ContainerIndexes.IndexTypeMap.items():
            try:
                container = new_containers[index]
            except IndexError:
                container = None

            if type_name == "definition":
                if not container or not isinstance(container, DefinitionContainer):
                    definition = self.findContainer(container_type = DefinitionContainer, category = "*")
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

    def _onContainersChanged(self, container):
        self.pyqtContainersChanged.emit()

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

    # Perform reverse lookup (type name -> index)
    @classmethod
    def indexForType(cls, type_name: str) -> int:
        for key, value in cls.IndexTypeMap.items():
            if value == type_name:
                return key

        return -1

