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

class GlobalStack(ContainerStack):
    def __init__(self, container_id: str, *args, **kwargs):
        super().__init__(container_id, *args, **kwargs)

        self._empty_instance_container = ContainerRegistry.getInstance().getEmptyInstanceContainer()

        self._extruders = []

        self.containersChanged.connect(self._onContainersChanged)

    pyqtContainersChanged = pyqtSignal()

    @pyqtProperty(InstanceContainer, notify = pyqtContainersChanged)
    def userChanges(self) -> InstanceContainer:
        return self._containers[_ContainerIndexes.UserChanges]

    def setQualtiyChanges(self, new_quality_changes: InstanceContainer) -> None:
        self.replaceContainer(_ContainerIndexes.QualityChanges, new_quality_changes)

    @pyqtProperty(InstanceContainer, notify = pyqtContainersChanged)
    def qualityChanges(self) -> InstanceContainer:
        return self._containers[_ContainerIndexes.QualityChanges]

    def setQuality(self, new_quality: InstanceContainer) -> None:
        self.replaceContainer(_ContainerIndexes.Quality, new_quality)

    @pyqtProperty(InstanceContainer, notify = pyqtContainersChanged)
    def quality(self) -> InstanceContainer:
        return self._containers[_ContainerIndexes.Quality]

    def setMaterial(self, new_material: InstanceContainer) -> None:
        self.replaceContainer(_ContainerIndexes.Material, new_material)

    @pyqtProperty(InstanceContainer, notify = pyqtContainersChanged)
    def material(self) -> InstanceContainer:
        return self._containers[_ContainerIndexes.Material]

    def setVariant(self, new_variant: InstanceContainer) -> None:
        self.replaceContainer(_ContainerIndexes.Variant, new_variant)

    @pyqtProperty(InstanceContainer, notify = pyqtContainersChanged)
    def variant(self) -> InstanceContainer:
        return self._containers[_ContainerIndexes.Variant]

    @pyqtProperty(InstanceContainer, notify = pyqtContainersChanged)
    def definitionChanges(self) -> InstanceContainer:
        return self._containers[_ContainerIndexes.DefinitionChanges]

    @pyqtProperty(DefinitionContainer)
    def definition(self) -> DefinitionContainer:
        return self._containers[_ContainerIndexes.Definition]

    @pyqtProperty("QVariantList")
    def extruders(self) -> list:
        return self._extruders

    def addExtruder(self, extruder):
        extruder_count = self.getProperty("machine_extruder_count", "value")
        if len(self._extruders) > extruder_count:
            raise Exceptions.TooManyExtrudersError("Tried to add extruder to {id} but its extruder count is {count}".format(id = self.id, count = extruder_count))

        self._extruders.append(extruder)

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

    ##  Overridden from ContainerStack
    @override(ContainerStack)
    def getProperty(self, key: str, property_name: str):
        if property_name == "value":
            if not self.hasUserValue(key):
                resolve = super().getProperty(key, "resolve")
                if resolve:
                    return resolve

        return super().getProperty(key, property_name)

    ##  Overridden from ContainerStack
    @override(ContainerStack)
    def setNextStack(self, next_stack: ContainerStack) -> None:
        raise Exceptions.InvalidOperationError("Global stack cannot have a next stack!")

    ##  Overridden from ContainerStack
    #
    #   Since we have a fixed order of containers in the stack, we want to enforce this.
    @override(ContainerStack)
    def addContainer(self, container: ContainerInterface) -> None:
        raise Exceptions.InvalidOperationError("Cannot add a container to Global stack")

    ##  Overridden from ContainerStack
    @override(ContainerStack)
    def insertContainer(self, index: int, container: ContainerInterface) -> None:
        raise Exceptions.InvalidOperationError("Cannot insert a container into Global stack")

    ##  Overridden from ContainerStack
    @override(ContainerStack)
    def removeContainer(self, index: int) -> None:
        raise Exceptions.InvalidOperationError("Cannot remove a container from Global stack")

    ##  Overridden from ContainerStack
    @override(ContainerStack)
    def replaceContainer(self, index: int, container: ContainerInterface, postpone_emit: bool = False) -> None:
        expected_type = _ContainerIndexes.IndexTypeMap[index]
        if expected_type == "definition" and not isinstance(container, DefinitionContainer):
            raise Exceptions.InvalidContainerError("Cannot replace container at index {index} with a container that is not a DefinitionContainer".format(index = index))
        if container != self._empty_instance_container and container.getMetaDataEntry("type") != expected_type:
            raise Exceptions.InvalidContainerError("Cannot replace container at index {index} with a container that is not of {type} type".format(index = index, type = expected_type))

        super().replaceContainer(index, container, postpone_emit)

    ##  Overridden from ContainerStack
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

        self._containers = new_containers

    def _onContainersChanged(self, container):
        self.pyqtContainersChanged.emit()

## private:
global_stack_mime = MimeType(
    name = "application/x-cura-globalstack",
    comment = "Cura Global Stack",
    suffixes = ["global.cfg"]
)

MimeTypeDatabase.addMimeType(global_stack_mime)
ContainerRegistry.addContainerTypeByName(GlobalStack, "global_stack", global_stack_mime.name)


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
