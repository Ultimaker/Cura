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
from .CuraContainerStack import CuraContainerStack

class GlobalStack(CuraContainerStack):
    def __init__(self, container_id: str, *args, **kwargs):
        super().__init__(container_id, *args, **kwargs)

        self._extruders = []

        self._resolving_property = None

    @pyqtProperty("QVariantList")
    def extruders(self) -> list:
        return self._extruders

    def addExtruder(self, extruder):
        extruder_count = self.getProperty("machine_extruder_count", "value")
        if len(self._extruders) + 1 > extruder_count:
            raise Exceptions.TooManyExtrudersError("Tried to add extruder to {id} but its extruder count is {count}".format(id = self.id, count = extruder_count))

        self._extruders.append(extruder)

    ##  Overridden from ContainerStack
    @override(ContainerStack)
    def getProperty(self, key: str, property_name: str) -> Any:
        if property_name == "value" and not self._resolving_property:
            if not self.hasUserValue(key):
                self._resolving_property = key
                resolve = super().getProperty(key, "resolve")
                if resolve:
                    return resolve

        return super().getProperty(key, property_name)

    ##  Overridden from ContainerStack
    @override(ContainerStack)
    def setNextStack(self, next_stack: ContainerStack) -> None:
        raise Exceptions.InvalidOperationError("Global stack cannot have a next stack!")


## private:
global_stack_mime = MimeType(
    name = "application/x-cura-globalstack",
    comment = "Cura Global Stack",
    suffixes = ["global.cfg"]
)

MimeTypeDatabase.addMimeType(global_stack_mime)
ContainerRegistry.addContainerTypeByName(GlobalStack, "global_stack", global_stack_mime.name)
