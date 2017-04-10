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

        self.addMetaDataEntry("type", "machine") # For backward compatibility

        self._extruders = []

        # This property is used to track which settings we are calculating the "resolve" for
        # and if so, to bypass the resolve to prevent an infinite recursion that would occur
        # if the resolve function tried to access the same property it is a resolve for.
        self._resolving_settings = set()

    @pyqtProperty("QVariantList")
    def extruders(self) -> list:
        return self._extruders

    def addExtruder(self, extruder):
        extruder_count = self.getProperty("machine_extruder_count", "value")
        if extruder_count and len(self._extruders) + 1 > extruder_count:
            raise Exceptions.TooManyExtrudersError("Tried to add extruder to {id} but its extruder count is {count}".format(id = self.id, count = extruder_count))

        self._extruders.append(extruder)

    ##  Overridden from ContainerStack
    @override(ContainerStack)
    def getProperty(self, key: str, property_name: str) -> Any:
        if not self.definition.findDefinitions(key = key):
            return None

        if self._shouldResolve(key, property_name):
            self._resolving_settings.add(key)
            resolve = super().getProperty(key, "resolve")
            self._resolving_settings.remove(key)
            if resolve is not None:
                return resolve

        return super().getProperty(key, property_name)

    ##  Overridden from ContainerStack
    @override(ContainerStack)
    def setNextStack(self, next_stack: ContainerStack) -> None:
        raise Exceptions.InvalidOperationError("Global stack cannot have a next stack!")

    def _shouldResolve(self, key: str, property_name: str) -> bool:
        if property_name is not "value":
            # Do not try to resolve anything but the "value" property
            return False

        if key in self._resolving_settings:
            # To prevent infinite recursion, if getProperty is called with the same key as
            # we are already trying to resolve, we should not try to resolve again. Since
            # this can happen multiple times when trying to resolve a value, we need to
            # track all settings that are being resolved.
            return False

        if self.hasUserValue(key):
            # When the user has explicitly set a value, we should ignore any resolve and
            # just return that value.
            return False

        return True


## private:
global_stack_mime = MimeType(
    name = "application/x-cura-globalstack",
    comment = "Cura Global Stack",
    suffixes = ["global.cfg"]
)

MimeTypeDatabase.addMimeType(global_stack_mime)
ContainerRegistry.addContainerTypeByName(GlobalStack, "global_stack", global_stack_mime.name)
