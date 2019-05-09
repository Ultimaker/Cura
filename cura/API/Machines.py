# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, Dict, TYPE_CHECKING
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, pyqtProperty
from UM.i18n import i18nCatalog
from UM.Logger import Logger
if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication

i18n_catalog = i18nCatalog("cura")

##  The account API provides a version-proof bridge to use Ultimaker Accounts
#
#   Usage:
#       ```
#       from cura.API import CuraAPI
#       api = CuraAPI()
#       api.machines.addOutputDeviceToCurrentMachine()
#       ```
#
class Machines(QObject):

    def __init__(self, application: "CuraApplication", parent = None) -> None:
        super().__init__(parent)
        self._application = application

    ##  Add an output device to the current machine.
    #   In practice, this means:
    #   - Setting the output device's network key in the current machine's metadata
    #   - Adding the output device's connection type to the current machine's configured connection
    #     types.
    #   TODO: CHANGE TO HOSTNAME
    @pyqtSlot(QObject)
    def addOutputDeviceToCurrentMachine(self, output_device):
        if not output_device:
            return

        Logger.log("d",
            "Attempting to set the network key of the active machine to %s",
            output_device.key)

        global_container_stack = self._application.getGlobalContainerStack()
        if not global_container_stack:
            return

        metadata = global_container_stack.getMetaData()

        if "um_network_key" in metadata:  # Global stack already had a connection, but it's changed.
            old_network_key = metadata["um_network_key"]
            # Since we might have a bunch of hidden stacks, we also need to change it there.
            metadata_filter = {"um_network_key": old_network_key}
            containers = self._application.getContainerRegistry().findContainerStacks(
                type = "machine", **metadata_filter)

            for container in containers:
                container.setMetaDataEntry("um_network_key", output_device.key)

                # Delete old authentication data.
                Logger.log("d", "Removing old authentication id %s for device %s",
                    global_container_stack.getMetaDataEntry("network_authentication_id", None),
                    output_device.key)

                container.removeMetaDataEntry("network_authentication_id")
                container.removeMetaDataEntry("network_authentication_key")

                # Ensure that these containers do know that they are configured for the given
                # connection type (can be more than one type; e.g. LAN & Cloud)
                container.addConfiguredConnectionType(output_device.connectionType.value)

        else:  # Global stack didn't have a connection yet, configure it.
            global_container_stack.setMetaDataEntry("um_network_key", output_device.key)
            global_container_stack.addConfiguredConnectionType(output_device.connectionType.value)

        return None
    
