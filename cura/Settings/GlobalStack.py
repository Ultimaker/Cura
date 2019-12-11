# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from collections import defaultdict
import threading
from typing import Any, Dict, Optional, Set, TYPE_CHECKING, List
import uuid

from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal

from UM.Decorators import deprecated, override
from UM.MimeTypeDatabase import MimeType, MimeTypeDatabase
from UM.Settings.ContainerStack import ContainerStack
from UM.Settings.SettingInstance import InstanceState
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.Interfaces import PropertyEvaluationContext
from UM.Logger import Logger
from UM.Resources import Resources
from UM.Platform import Platform
from UM.Util import parseBool

import cura.CuraApplication
from cura.PrinterOutput.PrinterOutputDevice import ConnectionType

from . import Exceptions
from .CuraContainerStack import CuraContainerStack

if TYPE_CHECKING:
    from cura.Settings.ExtruderStack import ExtruderStack


##  Represents the Global or Machine stack and its related containers.
#
class GlobalStack(CuraContainerStack):
    def __init__(self, container_id: str) -> None:
        super().__init__(container_id)

        self.setMetaDataEntry("type", "machine")  # For backward compatibility

        # TL;DR: If Cura is looking for printers that belong to the same group, it should use "group_id".
        # Each GlobalStack by default belongs to a group which is identified via "group_id". This group_id is used to
        # figure out which GlobalStacks are in the printer cluster for example without knowing the implementation
        # details such as the um_network_key or some other identifier that's used by the underlying device plugin.
        self.setMetaDataEntry("group_id", str(uuid.uuid4()))  # Assign a new GlobalStack to a unique group by default

        self._extruders = {}  # type: Dict[str, "ExtruderStack"]

        # This property is used to track which settings we are calculating the "resolve" for
        # and if so, to bypass the resolve to prevent an infinite recursion that would occur
        # if the resolve function tried to access the same property it is a resolve for.
        # Per thread we have our own resolving_settings, or strange things sometimes occur.
        self._resolving_settings = defaultdict(set) #type: Dict[str, Set[str]] # keys are thread names

        # Since the metadatachanged is defined in container stack, we can't use it here as a notifier for pyqt
        # properties. So we need to tie them together like this.
        self.metaDataChanged.connect(self.configuredConnectionTypesChanged)

    extrudersChanged = pyqtSignal()
    configuredConnectionTypesChanged = pyqtSignal()

    ##  Get the list of extruders of this stack.
    #
    #   \return The extruders registered with this stack.
    @pyqtProperty("QVariantMap", notify = extrudersChanged)
    @deprecated("Please use extruderList instead.", "4.4")
    def extruders(self) -> Dict[str, "ExtruderStack"]:
        return self._extruders

    @pyqtProperty("QVariantList", notify = extrudersChanged)
    def extruderList(self) -> List["ExtruderStack"]:
        result_tuple_list = sorted(list(self._extruders.items()), key=lambda x: int(x[0]))
        result_list = [item[1] for item in result_tuple_list]

        machine_extruder_count = self.getProperty("machine_extruder_count", "value")
        return result_list[:machine_extruder_count]

    @pyqtProperty(int, constant = True)
    def maxExtruderCount(self):
        return len(self.getMetaDataEntry("machine_extruder_trains"))

    @pyqtProperty(bool, notify=configuredConnectionTypesChanged)
    def supportsNetworkConnection(self):
        return self.getMetaDataEntry("supports_network_connection", False)

    @classmethod
    def getLoadingPriority(cls) -> int:
        return 2

    ##  The configured connection types can be used to find out if the global
    #   stack is configured to be connected with a printer, without having to
    #   know all the details as to how this is exactly done (and without
    #   actually setting the stack to be active).
    #
    #   This data can then in turn also be used when the global stack is active;
    #   If we can't get a network connection, but it is configured to have one,
    #   we can display a different icon to indicate the difference.
    @pyqtProperty("QVariantList", notify=configuredConnectionTypesChanged)
    def configuredConnectionTypes(self) -> List[int]:
        # Requesting it from the metadata actually gets them as strings (as that's what you get from serializing).
        # But we do want them returned as a list of ints (so the rest of the code can directly compare)
        connection_types = self.getMetaDataEntry("connection_type", "").split(",")
        result = []
        for connection_type in connection_types:
            if connection_type != "":
                try:
                    result.append(int(connection_type))
                except ValueError:
                    # We got invalid data, probably a None.
                    pass
        return result

    # Returns a boolean indicating if this machine has a remote connection. A machine is considered as remotely
    # connected if its connection types contain one of the following values:
    #   - ConnectionType.NetworkConnection
    #   - ConnectionType.CloudConnection
    @pyqtProperty(bool, notify = configuredConnectionTypesChanged)
    def hasRemoteConnection(self) -> bool:
        has_remote_connection = False

        for connection_type in self.configuredConnectionTypes:
            has_remote_connection |= connection_type in [ConnectionType.NetworkConnection.value,
                                                         ConnectionType.CloudConnection.value]
        return has_remote_connection

    ##  \sa configuredConnectionTypes
    def addConfiguredConnectionType(self, connection_type: int) -> None:
        configured_connection_types = self.configuredConnectionTypes
        if connection_type not in configured_connection_types:
            # Store the values as a string.
            configured_connection_types.append(connection_type)
            self.setMetaDataEntry("connection_type", ",".join([str(c_type) for c_type in configured_connection_types]))

    ##  \sa configuredConnectionTypes
    def removeConfiguredConnectionType(self, connection_type: int) -> None:
        configured_connection_types = self.configuredConnectionTypes
        if connection_type in configured_connection_types:
            # Store the values as a string.
            configured_connection_types.remove(connection_type)
            self.setMetaDataEntry("connection_type", ",".join([str(c_type) for c_type in configured_connection_types]))

    @classmethod
    def getConfigurationTypeFromSerialized(cls, serialized: str) -> Optional[str]:
        configuration_type = super().getConfigurationTypeFromSerialized(serialized)
        if configuration_type == "machine":
            return "machine_stack"
        return configuration_type

    def getIntentCategory(self) -> str:
        intent_category = "default"
        for extruder in self.extruderList:
            category = extruder.intent.getMetaDataEntry("intent_category", "default")
            if category != "default" and category != intent_category:
                intent_category = category
        return intent_category

    def getBuildplateName(self) -> Optional[str]:
        name = None
        if self.variant.getId() != "empty_variant":
            name = self.variant.getName()
        return name

    @pyqtProperty(str, constant = True)
    def preferred_output_file_formats(self) -> str:
        return self.getMetaDataEntry("file_formats")

    ##  Add an extruder to the list of extruders of this stack.
    #
    #   \param extruder The extruder to add.
    #
    #   \throws Exceptions.TooManyExtrudersError Raised when trying to add an extruder while we
    #                                            already have the maximum number of extruders.
    def addExtruder(self, extruder: ContainerStack) -> None:
        position = extruder.getMetaDataEntry("position")
        if position is None:
            Logger.log("w", "No position defined for extruder {extruder}, cannot add it to stack {stack}", extruder = extruder.id, stack = self.id)
            return

        if any(item.getId() == extruder.id for item in self._extruders.values()):
            Logger.log("w", "Extruder [%s] has already been added to this stack [%s]", extruder.id, self.getId())
            return

        self._extruders[position] = extruder
        self.extrudersChanged.emit()
        Logger.log("i", "Extruder[%s] added to [%s] at position [%s]", extruder.id, self.id, position)

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
    def getProperty(self, key: str, property_name: str, context: Optional[PropertyEvaluationContext] = None) -> Any:
        if not self.definition.findDefinitions(key = key):
            return None

        if context is None:
            context = PropertyEvaluationContext()
        context.pushContainer(self)

        # Handle the "resolve" property.
        #TODO: Why the hell does this involve threading?
        # Answer: Because if multiple threads start resolving properties that have the same underlying properties that's
        # related, without taking a note of which thread a resolve paths belongs to, they can bump into each other and
        # generate unexpected behaviours.
        if self._shouldResolve(key, property_name, context):
            current_thread = threading.current_thread()
            self._resolving_settings[current_thread.name].add(key)
            resolve = super().getProperty(key, "resolve", context)
            self._resolving_settings[current_thread.name].remove(key)
            if resolve is not None:
                return resolve

        # Handle the "limit_to_extruder" property.
        limit_to_extruder = super().getProperty(key, "limit_to_extruder", context)
        if limit_to_extruder is not None:
            if limit_to_extruder == -1:
                limit_to_extruder = int(cura.CuraApplication.CuraApplication.getInstance().getMachineManager().defaultExtruderPosition)
            limit_to_extruder = str(limit_to_extruder)
        if limit_to_extruder is not None and limit_to_extruder != "-1" and limit_to_extruder in self._extruders:
            if super().getProperty(key, "settable_per_extruder", context):
                result = self._extruders[str(limit_to_extruder)].getProperty(key, property_name, context)
                if result is not None:
                    context.popContainer()
                    return result
            else:
                Logger.log("e", "Setting {setting} has limit_to_extruder but is not settable per extruder!", setting = key)

        result = super().getProperty(key, property_name, context)
        context.popContainer()
        return result

    ##  Overridden from ContainerStack
    #
    #   This will simply raise an exception since the Global stack cannot have a next stack.
    @override(ContainerStack)
    def setNextStack(self, stack: CuraContainerStack, connect_signals: bool = True) -> None:
        raise Exceptions.InvalidOperationError("Global stack cannot have a next stack!")

    # protected:

    # Determine whether or not we should try to get the "resolve" property instead of the
    # requested property.
    def _shouldResolve(self, key: str, property_name: str, context: Optional[PropertyEvaluationContext] = None) -> bool:
        if property_name != "value":
            # Do not try to resolve anything but the "value" property
            return False

        current_thread = threading.current_thread()
        if key in self._resolving_settings[current_thread.name]:
            # To prevent infinite recursion, if getProperty is called with the same key as
            # we are already trying to resolve, we should not try to resolve again. Since
            # this can happen multiple times when trying to resolve a value, we need to
            # track all settings that are being resolved.
            return False

        setting_state = super().getProperty(key, "state", context = context)
        if setting_state is not None and setting_state != InstanceState.Default:
            # When the user has explicitly set a value, we should ignore any resolve and
            # just return that value.
            return False

        return True

    ##  Perform some sanity checks on the global stack
    #   Sanity check for extruders; they must have positions 0 and up to machine_extruder_count - 1
    def isValid(self) -> bool:
        container_registry = ContainerRegistry.getInstance()
        extruder_trains = container_registry.findContainerStacks(type = "extruder_train", machine = self.getId())

        machine_extruder_count = self.getProperty("machine_extruder_count", "value")
        extruder_check_position = set()
        for extruder_train in extruder_trains:
            extruder_position = extruder_train.getMetaDataEntry("position")
            extruder_check_position.add(extruder_position)

        for check_position in range(machine_extruder_count):
            if str(check_position) not in extruder_check_position:
                return False
        return True

    def getHeadAndFansCoordinates(self):
        return self.getProperty("machine_head_with_fans_polygon", "value")

    @pyqtProperty(bool, constant = True)
    def hasMaterials(self) -> bool:
        return parseBool(self.getMetaDataEntry("has_materials", False))

    @pyqtProperty(bool, constant = True)
    def hasVariants(self) -> bool:
        return parseBool(self.getMetaDataEntry("has_variants", False))

    @pyqtProperty(bool, constant = True)
    def hasVariantBuildplates(self) -> bool:
        return parseBool(self.getMetaDataEntry("has_variant_buildplates", False))

    ##  Get default firmware file name if one is specified in the firmware
    @pyqtSlot(result = str)
    def getDefaultFirmwareName(self) -> str:
        machine_has_heated_bed = self.getProperty("machine_heated_bed", "value")

        baudrate = 250000
        if Platform.isLinux():
            # Linux prefers a baudrate of 115200 here because older versions of
            # pySerial did not support a baudrate of 250000
            baudrate = 115200

        # If a firmware file is available, it should be specified in the definition for the printer
        hex_file = self.getMetaDataEntry("firmware_file", None)
        if machine_has_heated_bed:
            hex_file = self.getMetaDataEntry("firmware_hbk_file", hex_file)

        if not hex_file:
            Logger.log("w", "There is no firmware for machine %s.", self.getBottom().id)
            return ""

        try:
            return Resources.getPath(cura.CuraApplication.CuraApplication.ResourceTypes.Firmware, hex_file.format(baudrate=baudrate))
        except FileNotFoundError:
            Logger.log("w", "Firmware file %s not found.", hex_file)
            return ""

    def getName(self) -> str:
        return self._metadata.get("group_name", self._metadata.get("name", ""))

    def setName(self, name: "str") -> None:
        super().setName(name)

    nameChanged = pyqtSignal()
    name = pyqtProperty(str, fget=getName, fset=setName, notify=nameChanged)



## private:
global_stack_mime = MimeType(
    name = "application/x-cura-globalstack",
    comment = "Cura Global Stack",
    suffixes = ["global.cfg"]
)

MimeTypeDatabase.addMimeType(global_stack_mime)
ContainerRegistry.addContainerTypeByName(GlobalStack, "global_stack", global_stack_mime.name)
