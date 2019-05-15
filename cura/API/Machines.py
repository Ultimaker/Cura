# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, Dict,  List, TYPE_CHECKING, Any
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, pyqtProperty
from UM.i18n import i18nCatalog
from UM.Logger import Logger
if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication
    from cura.PrinterOutput.PrinterOutputDevice import PrinterOutputDevice

i18n_catalog = i18nCatalog("cura")

##  The account API provides a version-proof bridge to use Ultimaker Accounts
#
#   Usage:
#       ```
#       from cura.API import CuraAPI
#       api = CuraAPI()
#       api.machines.addOutputDeviceToCurrentMachine()
#       ```

##  Since Cura doesn't have a machine class, we're going to make a fake one to make our lives a
#   little bit easier.
class Machine():
    def __init__(self) -> None:
        self.hostname = "" # type: str
        self.group_id = "" # type: str
        self.group_name = "" # type: str
        self.um_network_key = "" # type: str
        self.configuration = {} # type: Dict[str, Any]
        self.connection_types = [] # type: List[int]

class Machines(QObject):

    def __init__(self, application: "CuraApplication", parent = None) -> None:
        super().__init__(parent)
        self._application = application

    @pyqtSlot(result="QVariantMap")
    def getCurrentMachine(self) -> Machine:
        fake_machine = Machine() # type: Machine
        global_stack = self._application.getGlobalContainerStack()
        if global_stack:
            metadata = global_stack.getMetaData()
            if "group_id" in metadata:
                fake_machine.group_id = global_stack.getMetaDataEntry("group_id")
            if "group_name" in metadata:
                fake_machine.group_name = global_stack.getMetaDataEntry("group_name")
            if "um_network_key" in metadata:
                fake_machine.um_network_key = global_stack.getMetaDataEntry("um_network_key")

            fake_machine.connection_types = global_stack.configuredConnectionTypes
            
        return fake_machine

    ##  Set the current machine's friendy name.
    #   This is the same as "group name" since we use "group" and "current machine" interchangeably.
    #   TODO: Maybe make this "friendly name" to distinguish from "hostname"?
    @pyqtSlot(str)
    def setCurrentMachineGroupName(self, group_name: str) -> None:
        Logger.log("d", "Attempting to set the group name of the active machine to %s", group_name)
        global_stack = self._application.getGlobalContainerStack()
        if global_stack:
            # Update a GlobalStacks in the same group with the new group name.
            group_id = global_stack.getMetaDataEntry("group_id")
            machine_manager = self._application.getMachineManager()
            for machine in machine_manager.getMachinesInGroup(group_id):
                machine.setMetaDataEntry("group_name", group_name)

            # Set the default value for "hidden", which is used when you have a group with multiple types of printers
            global_stack.setMetaDataEntry("hidden", False)

    ##  Set the current machine's configuration from an (optional) output device.
    #   If no output device is given, the first one available on the machine will be used.
    #   NOTE: Group and machine are used interchangeably.
    #   NOTE: This doesn't seem to be used anywhere. Maybe delete?
    @pyqtSlot(QObject)
    def updateCurrentMachineConfiguration(self, output_device: Optional["PrinterOutputDevice"]) -> None:

        if output_device is None:
            machine_manager = self._application.getMachineManager()
            output_device = machine_manager.printerOutputDevices[0]
        
        hotend_ids = output_device.hotendIds
        for index in range(len(hotend_ids)):
            output_device.hotendIdChanged.emit(index, hotend_ids[index])
        
        material_ids = output_device.materialIds
        for index in range(len(material_ids)):
            output_device.materialIdChanged.emit(index, material_ids[index])

    ##  Add an output device to the current machine.
    #   In practice, this means:
    #   - Setting the output device's network key in the current machine's metadata
    #   - Adding the output device's connection type to the current machine's configured connection
    #     types.
    #   TODO: CHANGE TO HOSTNAME
    @pyqtSlot(QObject)
    def addOutputDeviceToCurrentMachine(self, output_device: "PrinterOutputDevice") -> None:
        if not output_device:
            return
        Logger.log("d",
            "Attempting to set the network key of the active machine to %s",
            output_device.key)
        global_stack = self._application.getGlobalContainerStack()
        if not global_stack:
            return
        metadata = global_stack.getMetaData()

        # Global stack already had a connection, but it's changed.
        if "um_network_key" in metadata: 
            old_network_key = metadata["um_network_key"]

            # Since we might have a bunch of hidden stacks, we also need to change it there.
            metadata_filter = {"um_network_key": old_network_key}
            containers = self._application.getContainerRegistry().findContainerStacks(
                type = "machine", **metadata_filter)
            for container in containers:
                container.setMetaDataEntry("um_network_key", output_device.key)

                # Delete old authentication data.
                Logger.log("d", "Removing old authentication id %s for device %s",
                    global_stack.getMetaDataEntry("network_authentication_id", None),
                    output_device.key)

                container.removeMetaDataEntry("network_authentication_id")
                container.removeMetaDataEntry("network_authentication_key")

                # Ensure that these containers do know that they are configured for the given
                # connection type (can be more than one type; e.g. LAN & Cloud)
                container.addConfiguredConnectionType(output_device.connectionType.value)

        else:  # Global stack didn't have a connection yet, configure it.
            global_stack.setMetaDataEntry("um_network_key", output_device.key)
            global_stack.addConfiguredConnectionType(output_device.connectionType.value)

        return None
    
