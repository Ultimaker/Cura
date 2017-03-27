# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot

from UM.MimeTypeDatabase import MimeType, MimeTypeDatabase
from UM.Settings.ContainerStack import ContainerStack
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.DefinitionContainer import DefinitionContainer

class ExtruderStack(ContainerStack):
    def __init__(self, container_id, *args, **kwargs):
        super().__init__(container_id, *args, **kwargs)

    @pyqtProperty(InstanceContainer)
    def userChanges(self) -> InstanceContainer:
        return self._containers[_ContainerIndexes.UserChanges]

    @pyqtProperty(InstanceContainer)
    def qualityChanges(self) -> InstanceContainer:
        return self._containers[_ContainerIndexes.QualityChanges]

    @pyqtProperty(InstanceContainer)
    def quality(self) -> InstanceContainer:
        return self._containers[_ContainerIndexes.Quality]

    @pyqtProperty(InstanceContainer)
    def material(self) -> InstanceContainer:
        return self._containers[_ContainerIndexes.Material]

    @pyqtProperty(InstanceContainer)
    def variant(self) -> InstanceContainer:
        return self._containers[_ContainerIndexes.Variant]

    @pyqtProperty(DefinitionContainer)
    def definition(self) -> DefinitionContainer:
        return self._containers[_ContainerIndexes.Definition]

extruder_stack_mime = MimeType(
    name = "application/x-cura-extruderstack",
    comment = "Cura Extruder Stack",
    suffixes = [ "extruder.cfg" ]
)

MimeTypeDatabase.addMimeType(extruder_stack_mime)
ContainerRegistry.addContainerTypeByName(ExtruderStack, "extruder_stack", extruder_stack_mime.name)

class _ContainerIndexes:
    UserChanges = 0
    QualityChanges = 1
    Quality = 2
    Material = 3
    Variant = 4
    Definition = 5

