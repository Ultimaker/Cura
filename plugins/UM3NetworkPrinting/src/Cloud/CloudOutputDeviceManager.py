# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import json
from time import sleep
from threading import Thread
from typing import Dict, Optional, List

from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply

from UM.Logger import Logger
from cura.CuraApplication import CuraApplication
from cura.NetworkClient import NetworkClient

from .CloudOutputDevice import CloudOutputDevice
from .Models import CloudCluster


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

    # The interval with wich the remote clusters are checked
    CHECK_CLUSTER_INTERVAL = 5  # seconds
    
    def __init__(self):
        super().__init__()

        # Persistent dict containing the remote clusters for the authenticated user.
        self._remote_clusters = {}  # type: Dict[str, CloudOutputDevice]

        application = CuraApplication.getInstance()
        self._output_device_manager = application.getOutputDeviceManager()
        self._account = application.getCuraAPI().account
        
        # When switching machines we check if we have to activate a remote cluster.
        application.globalContainerStackChanged.connect(self._activeMachineChanged)

        # Periodically check all remote clusters for the authenticated user.
        self._update_clusters_thread = Thread(target=self._updateClusters, daemon=True)
        self._update_clusters_thread.start()

    ##  Override _createEmptyRequest to add the needed authentication header for talking to the Ultimaker Cloud API.
    def _createEmptyRequest(self, path: str, content_type: Optional[str] = "application/json") -> QNetworkRequest:
        request = super()._createEmptyRequest(self.API_ROOT_PATH + path, content_type = content_type)
        if self._account.isLoggedIn:
            # TODO: add correct scopes to OAuth2 client to use remote connect API.
            # TODO: don't create the client when not signed in?
            request.setRawHeader(b"Authorization", "Bearer {}".format(self._account.accessToken).encode())
        return request

    ##  Update the clusters
    def _updateClusters(self) -> None:
        while True:
            self._getRemoteClusters()
            sleep(self.CHECK_CLUSTER_INTERVAL)
        
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
        found_clusters = self._parseStatusResponse(reply)
        if not found_clusters:
            return

        known_cluster_ids = set(self._remote_clusters.keys())
        found_cluster_ids = set(found_clusters.keys())

        # Add an output device for each new remote cluster.
        for cluster_id in found_cluster_ids.difference(known_cluster_ids):
            self._addCloudOutputDevice(found_clusters[cluster_id])

        # Remove output devices that are gone
        for cluster_id in known_cluster_ids.difference(found_cluster_ids):
            self._removeCloudOutputDevice(found_clusters[cluster_id])

        # For testing we add a dummy device:
        # self._addCloudOutputDevice(CloudCluster(cluster_id = "LJ0tciiuZZjarrXAvFLEZ6ox4Cvx8FvtXUlQv4vIhV6w"))

    @staticmethod
    def _parseStatusResponse(reply: QNetworkReply) -> Dict[str, CloudCluster]:
        try:
            return {c["cluster_id"]: CloudCluster(**c) for c in json.loads(reply.readAll().data().decode("utf-8"))}
        except UnicodeDecodeError:
            Logger.log("w", "Unable to read server response")
        except json.decoder.JSONDecodeError:
            Logger.logException("w", "Unable to decode JSON from reply.")
        except ValueError:
            Logger.logException("w", "Response was missing values.")
        return {}

    ##  Adds a CloudOutputDevice for each entry in the remote cluster list from the API.
    def _addCloudOutputDevice(self, cluster: CloudCluster):
        device = CloudOutputDevice(cluster.cluster_id)
        self._output_device_manager.addOutputDevice(device)
        self._remote_clusters[cluster.cluster_id] = device

    ##  Remove a CloudOutputDevice
    def _removeCloudOutputDevice(self, cluster: CloudCluster):
        self._output_device_manager.removeOutputDevice(cluster.cluster_id)
        del self._remote_clusters[cluster.cluster_id]

    ##  Callback for when the active machine was changed by the user.
    def _activeMachineChanged(self):
        active_machine = CuraApplication.getInstance().getGlobalContainerStack()
        if not active_machine:
            return

        local_device_id = active_machine.getMetaDataEntry("um_network_key")
        if local_device_id:
            active_output_device = CuraApplication.getInstance().getOutputDeviceManager().getActiveDevice()
            active_output_device.id
    
        stored_cluster_id = active_machine.getMetaDataEntry("um_cloud_cluster_id")
        if stored_cluster_id not in self._remote_clusters.keys():
            # Currently authenticated user does not have access to stored cluster or no user is signed in.
            return

        # We found the active machine as remote cluster so let's connect to it.
        self._remote_clusters.get(stored_cluster_id).connect()
