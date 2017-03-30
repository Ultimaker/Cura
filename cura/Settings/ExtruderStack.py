# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

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

    @override(ContainerStack)
    def setNextStack(self, stack):
        super().setNextStack(stack)
        stack.addExtruder(self)

extruder_stack_mime = MimeType(
    name = "application/x-cura-extruderstack",
    comment = "Cura Extruder Stack",
    suffixes = [ "extruder.cfg" ]
)

MimeTypeDatabase.addMimeType(extruder_stack_mime)
ContainerRegistry.addContainerTypeByName(ExtruderStack, "extruder_stack", extruder_stack_mime.name)
