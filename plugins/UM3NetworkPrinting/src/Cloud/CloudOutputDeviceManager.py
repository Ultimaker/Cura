# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import json
from time import sleep
from threading import Thread
from typing import Dict, Optional

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
class CloudOutputDeviceManager(NetworkClient):
    
    # The cloud URL to use for remote clusters.
    API_ROOT_PATH = "https://api-staging.ultimaker.com/connect/v1"

    # The interval with which the remote clusters are checked
    CHECK_CLUSTER_INTERVAL = 5  # seconds
    
    def __init__(self):
        super().__init__()

        # Persistent dict containing the remote clusters for the authenticated user.
        self._remote_clusters = {}  # type: Dict[str, CloudOutputDevice]

        application = CuraApplication.getInstance()
        self._output_device_manager = application.getOutputDeviceManager()
        self._account = application.getCuraAPI().account
        self._account.loginStateChanged.connect(self._getRemoteClusters)
        
        # When switching machines we check if we have to activate a remote cluster.
        application.globalContainerStackChanged.connect(self._connectToActiveMachine)
        
        # TODO: fix this
        # Periodically check all remote clusters for the authenticated user.
        # self._update_clusters_thread = Thread(target=self._updateClusters, daemon=True)
        # self._update_clusters_thread.start()

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
        Logger.log("i", "Retrieving remote clusters")
        self.get("/clusters", on_finished = self._onGetRemoteClustersFinished)

    ##  Callback for when the request for getting the clusters. is finished.
    def _onGetRemoteClustersFinished(self, reply: QNetworkReply) -> None:
        Logger.log("i", "Received remote clusters")

        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code > 204:
            Logger.log("w", "Got unexpected response while trying to get cloud cluster data: {}, {}"
                       .format(status_code, reply.readAll()))
            return

        # Parse the response (returns the "data" field from the body).
        found_clusters = self._parseStatusResponse(reply)
        Logger.log("i", "Parsed remote clusters to %s", found_clusters)
        if not found_clusters:
            return

        known_cluster_ids = set(self._remote_clusters.keys())
        found_cluster_ids = set(found_clusters.keys())

        # Add an output device for each new remote cluster.
        for cluster_id in found_cluster_ids.difference(known_cluster_ids):
            if found_clusters[cluster_id].is_online:
                self._addCloudOutputDevice(found_clusters[cluster_id])

        # Remove output devices that are gone
        for cluster_id in known_cluster_ids.difference(found_cluster_ids):
            self._removeCloudOutputDevice(found_clusters[cluster_id])

    @staticmethod
    def _parseStatusResponse(reply: QNetworkReply) -> Dict[str, CloudCluster]:
        try:
            response = bytes(reply.readAll()).decode()
            return {c["cluster_id"]: CloudCluster(**c) for c in json.loads(response)["data"]}
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
        if cluster.is_online:
            # We found a new online cluster, we might need to connect to it.
            self._connectToActiveMachine()

    ##  Remove a CloudOutputDevice
    def _removeCloudOutputDevice(self, cluster: CloudCluster):
        self._output_device_manager.removeOutputDevice(cluster.cluster_id)
        del self._remote_clusters[cluster.cluster_id]

    ##  Callback for when the active machine was changed by the user.
    def _connectToActiveMachine(self) -> None:
        active_machine = CuraApplication.getInstance().getGlobalContainerStack()
        if not active_machine:
            return
        
        # Check if the stored cluster_id for the active machine is in our list of remote clusters.
        stored_cluster_id = active_machine.getMetaDataEntry("um_cloud_cluster_id")
        if stored_cluster_id in self._remote_clusters.keys():
            self._remote_clusters.get(stored_cluster_id).connect()
            return

        # TODO: See if this cloud cluster still has to be associated to the active machine.
        # TODO: We have to get a common piece of data, like local network hostname, from the active machine and
        # TODO: cloud cluster and then set the "um_cloud_cluster_id" meta data key on the active machine.
        # TODO: If so, we can also immediate connect to it.
        # active_machine.setMetaDataEntry("um_cloud_cluster_id", "")
        # self._remote_clusters.get(stored_cluster_id).connect()
