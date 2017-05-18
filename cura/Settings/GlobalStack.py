# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from typing import Any, Dict

from PyQt5.QtCore import pyqtProperty

from UM.Decorators import override

from UM.MimeTypeDatabase import MimeType, MimeTypeDatabase
from UM.Settings.ContainerStack import ContainerStack
from UM.Settings.SettingInstance import InstanceState
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Logger import Logger

from . import Exceptions
from .CuraContainerStack import CuraContainerStack

##  Represents the Global or Machine stack and its related containers.
#
class GlobalStack(CuraContainerStack):
    def __init__(self, container_id: str, *args, **kwargs):
        super().__init__(container_id, *args, **kwargs)

        self.addMetaDataEntry("type", "machine") # For backward compatibility

        self._extruders = {}

        # This property is used to track which settings we are calculating the "resolve" for
        # and if so, to bypass the resolve to prevent an infinite recursion that would occur
        # if the resolve function tried to access the same property it is a resolve for.
        self._resolving_settings = set()

    ##  Get the list of extruders of this stack.
    #
    #   \return The extruders registered with this stack.
    @pyqtProperty("QVariantMap")
    def extruders(self) -> Dict[str, "ExtruderStack"]:
        return self._extruders

    @classmethod
    def getLoadingPriority(cls) -> int:
        return 2

    ##  Add an extruder to the list of extruders of this stack.
    #
    #   \param extruder The extruder to add.
    #
    #   \throws Exceptions.TooManyExtrudersError Raised when trying to add an extruder while we
    #                                            already have the maximum number of extruders.
    def addExtruder(self, extruder: ContainerStack) -> None:
        extruder_count = self.getProperty("machine_extruder_count", "value")
        if extruder_count and len(self._extruders) + 1 > extruder_count:
            Logger.log("w", "Adding extruder {meta} to {id} but its extruder count is {count}".format(id = self.id, count = extruder_count, meta = str(extruder.getMetaData())))
            return

        position = extruder.getMetaDataEntry("position")
        if position is None:
            Logger.log("w", "No position defined for extruder {extruder}, cannot add it to stack {stack}", extruder = extruder.id, stack = self.id)
            return

        if any(item.getId() == extruder.id for item in self._extruders.values()):
            Logger.log("w", "Extruder [%s] has already been added to this stack [%s]", extruder.id, self._id)
            return
        self._extruders[position] = extruder

    ##  Overridden from ContainerStack
    #
    #   This will return the value of the specified property for the specified setting,
    #   unless the property is "value" and that setting has a "resolve" function set.
    #   When a resolve is set, it will instead try and execute the resolve first and
    #   then fall back to the normal "value" property.
    #
    #   \param key The setting key to get the property of.
    #   \param property_name The property to get the value of.
    #
    #   \return The value of the property for the specified setting, or None if not found.
    @override(ContainerStack)
    def getProperty(self, key: str, property_name: str) -> Any:
        if not self.definition.findDefinitions(key = key):
            return None

        # Handle the "resolve" property.
        if self._shouldResolve(key, property_name):
            self._resolving_settings.add(key)
            resolve = super().getProperty(key, "resolve")
            self._resolving_settings.remove(key)
            if resolve is not None:
                return resolve

        # Handle the "limit_to_extruder" property.
        limit_to_extruder = super().getProperty(key, "limit_to_extruder")
        if limit_to_extruder is not None and limit_to_extruder != "-1" and limit_to_extruder in self._extruders:
            if super().getProperty(key, "settable_per_extruder"):
                result = self._extruders[str(limit_to_extruder)].getProperty(key, property_name)
                if result is not None:
                    return result
            else:
                Logger.log("e", "Setting {setting} has limit_to_extruder but is not settable per extruder!", setting = key)

        return super().getProperty(key, property_name)

    ##  Overridden from ContainerStack
    #
    #   This will simply raise an exception since the Global stack cannot have a next stack.
    @override(ContainerStack)
    def setNextStack(self, next_stack: ContainerStack) -> None:
        raise Exceptions.InvalidOperationError("Global stack cannot have a next stack!")

    # protected:

    # Determine whether or not we should try to get the "resolve" property instead of the
    # requested property.
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

        setting_state = super().getProperty(key, "state")
        if setting_state is not None and setting_state != InstanceState.Default:
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
