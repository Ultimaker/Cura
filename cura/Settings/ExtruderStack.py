# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from typing import Any

from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot

from UM.Decorators import override
from UM.MimeTypeDatabase import MimeType, MimeTypeDatabase
from UM.Settings.ContainerStack import ContainerStack, InvalidContainerStackError
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.Interfaces import ContainerInterface

from . import Exceptions
from .CuraContainerStack import CuraContainerStack

class ExtruderStack(CuraContainerStack):
    def __init__(self, container_id, *args, **kwargs):
        super().__init__(container_id, *args, **kwargs)

        self.addMetaDataEntry("type", "extruder_train") # For backward compatibility

    @override(ContainerStack)
    def setNextStack(self, stack: ContainerStack) -> None:
        super().setNextStack(stack)
        stack.addExtruder(self)

    @override(ContainerStack)
    def getProperty(self, key: str, property_name: str) -> Any:
        if not self._next_stack:
            raise Exceptions.NoGlobalStackError("Extruder {id} is missing the next stack!".format(id = self.id))

        if not super().getProperty(key, "settable_per_extruder"):
            return self.getNextStack().getProperty(key, property_name)

        return super().getProperty(key, property_name)


extruder_stack_mime = MimeType(
    name = "application/x-cura-extruderstack",
    comment = "Cura Extruder Stack",
    suffixes = ["extruder.cfg"]
)

MimeTypeDatabase.addMimeType(extruder_stack_mime)
ContainerRegistry.addContainerTypeByName(ExtruderStack, "extruder_stack", extruder_stack_mime.name)
