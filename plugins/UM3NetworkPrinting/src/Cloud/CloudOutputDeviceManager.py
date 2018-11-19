# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import TYPE_CHECKING, Dict

from plugins.UM3NetworkPrinting.src.Cloud.CloudOutputDevice import CloudOutputDevice


if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication
    

##  The cloud output device manager is responsible for using the Ultimaker Cloud APIs to manage remote clusters.
#   Keeping all cloud related logic in this class instead of the UM3OutputDevicePlugin results in more readable code.
#
#   API spec is available on https://api.ultimaker.com/docs/connect/spec/.
#
#   TODO: figure out how to pair remote clusters, local networked clusters and local cura printer presets.
#   TODO: for now we just have multiple output devices if the cluster is available both locally and remote.
class CloudOutputDeviceManager:
    
    # The cloud URL to use for remote clusters.
    API_ROOT_PATH = "https://api-staging.ultimaker.com/connect/v1"
    
    def __init__(self, application: "CuraApplication"):
        self._application = application
        self._output_device_manager = application.getOutputDeviceManager()
        self._account = application.getCuraAPI().account
        
        # Persistent dict containing the remote clusters for the authenticated user.
        self._remote_clusters = {}  # type: Dict[str, CloudOutputDevice]
        
        # When switching machines we check if we have to activate a remote cluster.
        self._application.globalContainerStackChanged.connect(self._activeMachineChanged)
        
        # Fetch all remote clusters for the authenticated user.
        self._getRemoteClusters()
        
    ##  Gets all remote clusters from the API.
    def _getRemoteClusters(self):
        # TODO: get list of remote clusters and create an output device for each.
        # For testing we add a dummy device:
        self._addCloudOutputDevice({"cluster_id": "LJ0tciiuZZjarrXAvFLEZ6ox4Cvx8FvtXUlQv4vIhV6w"})
    
    ##  Adds a CloudOutputDevice for each entry in the remote cluster list from the API.
    def _addCloudOutputDevice(self, cluster_data: Dict[str, any]):
        # TODO: use model or named tuple for cluster_data
        device = CloudOutputDevice(cluster_data["cluster_id"])
        self._output_device_manager.addOutputDevice(device)
        self._remote_clusters[cluster_data["cluster_id"]] = device
    
    ##  Callback for when the active machine was changed by the user.
    def _activeMachineChanged(self):
        active_machine = self._application.getGlobalContainerStack()
        if not active_machine:
            return
    
        stored_cluster_id = active_machine.getMetaDataEntry("um_cloud_cluster_id")
        if stored_cluster_id not in self._remote_clusters.keys():
            # Currently authenticated user does not have access to stored cluster or no user is signed in.
            return

        # We found the active machine as remote cluster so let's connect to it.
        self._remote_clusters.get(stored_cluster_id).connect()
