# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import json
from typing import TYPE_CHECKING, Dict, Optional

from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply

from UM.Logger import Logger
from cura.NetworkClient import NetworkClient
from plugins.UM3NetworkPrinting.src.Cloud.CloudOutputDevice import CloudOutputDevice
    

##  The cloud output device manager is responsible for using the Ultimaker Cloud APIs to manage remote clusters.
#   Keeping all cloud related logic in this class instead of the UM3OutputDevicePlugin results in more readable code.
#
#   API spec is available on https://api.ultimaker.com/docs/connect/spec/.
#
#   TODO: figure out how to pair remote clusters, local networked clusters and local cura printer presets.
#   TODO: for now we just have multiple output devices if the cluster is available both locally and remote.
class CloudOutputDeviceManager(NetworkClient):
    
    # The cloud URL to use for remote clusters.
    API_ROOT_PATH = "https://api.ultimaker.com/connect/v1"
    
    def __init__(self):
        super().__init__()
        
        self._output_device_manager = self._application.getOutputDeviceManager()
        self._account = self._application.getCuraAPI().account
        
        # Persistent dict containing the remote clusters for the authenticated user.
        self._remote_clusters = {}  # type: Dict[str, CloudOutputDevice]
        
        # When switching machines we check if we have to activate a remote cluster.
        self._application.globalContainerStackChanged.connect(self._activeMachineChanged)

        # Fetch all remote clusters for the authenticated user.
        # TODO: update remote clusters periodically
        self._account.loginStateChanged.connect(self._getRemoteClusters)

    ##  Override _createEmptyRequest to add the needed authentication header for talking to the Ultimaker Cloud API.
    def _createEmptyRequest(self, path: str, content_type: Optional[str] = "application/json") -> QNetworkRequest:
        request = super()._createEmptyRequest(self.API_ROOT_PATH + path, content_type = content_type)
        if self._account.isLoggedIn:
            # TODO: add correct scopes to OAuth2 client to use remote connect API.
            # TODO: don't create the client when not signed in?
            request.setRawHeader(b"Authorization", "Bearer {}".format(self._account.accessToken).encode())
        return request
        
    ##  Gets all remote clusters from the API.
    def _getRemoteClusters(self) -> None:
        self.get("/clusters", on_finished = self._onGetRemoteClustersFinished)

    ##  Callback for when the request for getting the clusters. is finished.
    def _onGetRemoteClustersFinished(self, reply: QNetworkReply) -> None:
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code != 200:
            Logger.log("w", "Got unexpected response while trying to get cloud cluster data: {}, {}"
                       .format(status_code, reply.readAll()))
            return

        # Parse the response (returns the "data" field from the body).
        clusters_data = self._parseStatusResponse(reply)
        if not clusters_data:
            return
        
        # Add an output device for each remote cluster.
        # The clusters are an array of objects in a field called "data".
        for cluster in clusters_data:
            self._addCloudOutputDevice(cluster)
        
        # # For testing we add a dummy device:
        # self._addCloudOutputDevice({ "cluster_id": "LJ0tciiuZZjarrXAvFLEZ6ox4Cvx8FvtXUlQv4vIhV6w" })

    @staticmethod
    def _parseStatusResponse(reply: QNetworkReply) -> Optional[dict]:
        try:
            result = json.loads(bytes(reply.readAll()).decode("utf-8"))
            # TODO: use model or named tuple here.
            return result.data
        except json.decoder.JSONDecodeError:
            Logger.logException("w", "Unable to decode JSON from reply.")
            return None
    
    ##  Adds a CloudOutputDevice for each entry in the remote cluster list from the API.
    def _addCloudOutputDevice(self, cluster_data: Dict[str, any]):
        # TODO: use model or named tuple for cluster_data
        print("cluster_data====", cluster_data)
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
