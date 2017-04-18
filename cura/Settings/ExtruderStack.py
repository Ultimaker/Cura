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
from .ExtruderManager import ExtruderManager

##  Represents an Extruder and its related containers.
#
#
class ExtruderStack(CuraContainerStack):
    def __init__(self, container_id, *args, **kwargs):
        super().__init__(container_id, *args, **kwargs)

        self.addMetaDataEntry("type", "extruder_train") # For backward compatibility

    ##  Overridden from ContainerStack
    #
    #   This will set the next stack and ensure that we register this stack as an extruder.
    @override(ContainerStack)
    def setNextStack(self, stack: ContainerStack) -> None:
        super().setNextStack(stack)
        stack.addExtruder(self)
        if not self.getMetaDataEntry("machine"):
            self.addMetaDataEntry("machine", stack.id)
        else:
            self.setMetaDataEntry("machine", stack.id)

        # For backward compatibility: Register the extruder with the Extruder Manager
        ExtruderManager.getInstance().registerExtruder(self, stack.id)

    ##  Overridden from ContainerStack
    #
    #   It will perform a few extra checks when trying to get properties.
    #
    #   The two extra checks it currently does is to ensure a next stack is set and to bypass
    #   the extruder when the property is not settable per extruder.
    #
    #   \throws Exceptions.NoGlobalStackError Raised when trying to get a property from an extruder without
    #                                         having a next stack set.
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
