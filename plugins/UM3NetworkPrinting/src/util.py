
from typing import Any, Dict, Optional

from UM.Logger import Logger


# Finds all machines (GlobalStacks) with the given network_key or group_name and update the metadata of those
# machines with the key/values in the given metadata dict.
# Note that the old authentication data "network_authentication_id" and "network_authentication_key" will be
# deleted if found.
def updateMetadataForNetworkGroupMachines(network_key: Optional[str], group_name: Optional[str],
                                          new_metadata: Dict[str, Any]) -> None:
    # Either match with network_key or group_name
    filter_dict = {}
    if network_key is not None:
        filter_dict["um_network_key"] = network_key
    if group_name is not None:
        filter_dict["connect_group_name"] = group_name

    from cura.CuraApplication import CuraApplication

    active_global_stack = CuraApplication.getInstance().getMachineManager().activeMachine
    container_registry = CuraApplication.getInstance().getContainerRegistry()
    global_stack_list = container_registry.findContainerStacks(type = "machine", **filter_dict)
    if active_global_stack is not None and active_global_stack not in global_stack_list:
        global_stack_list.append(active_global_stack)
    for global_stack in global_stack_list:
        for key, value in new_metadata.items():
            global_stack.setMetaDataEntry(key, value)

        # Delete old authentication data.
        if network_key is not None:
            Logger.log("d", "Removing old authentication id %s for device %s",
                       global_stack.getMetaDataEntry("network_authentication_id", None),
                       network_key)
            global_stack.removeMetaDataEntry("network_authentication_id")
            global_stack.removeMetaDataEntry("network_authentication_key")
