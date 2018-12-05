# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Dict, List, Optional

from PyQt5.QtCore import QTimer

from UM import i18nCatalog
from UM.Logger import Logger
from UM.Message import Message
from cura.CuraApplication import CuraApplication
from .CloudApiClient import CloudApiClient
from .CloudOutputDevice import CloudOutputDevice
from .Models.CloudCluster import CloudCluster
from .Models.CloudErrorObject import CloudErrorObject


##  The cloud output device manager is responsible for using the Ultimaker Cloud APIs to manage remote clusters.
#   Keeping all cloud related logic in this class instead of the UM3OutputDevicePlugin results in more readable code.
#
#   API spec is available on https://api.ultimaker.com/docs/connect/spec/.
#
class CloudOutputDeviceManager:

    # The interval with which the remote clusters are checked
    CHECK_CLUSTER_INTERVAL = 5.0  # seconds

    # The translation catalog for this device.
    I18N_CATALOG = i18nCatalog("cura")

    def __init__(self):
        super().__init__()

        # Persistent dict containing the remote clusters for the authenticated user.
        self._remote_clusters = {}  # type: Dict[str, CloudOutputDevice]

        application = CuraApplication.getInstance()
        self._output_device_manager = application.getOutputDeviceManager()

        self._account = application.getCuraAPI().account
        self._account.loginStateChanged.connect(self._getRemoteClusters)
        self._api = CloudApiClient(self._account, self._onApiError)

        # When switching machines we check if we have to activate a remote cluster.
        application.globalContainerStackChanged.connect(self._connectToActiveMachine)
        
        self.update_timer = QTimer(CuraApplication.getInstance())
        self.update_timer.setInterval(self.CHECK_CLUSTER_INTERVAL * 1000)
        self.update_timer.setSingleShot(False)
        self.update_timer.timeout.connect(self._getRemoteClusters)

    ##  Gets all remote clusters from the API.
    def _getRemoteClusters(self) -> None:
        Logger.log("i", "Retrieving remote clusters")
        if self._account.isLoggedIn:
            self._api.getClusters(self._onGetRemoteClustersFinished)

        # Only start the polling timer after the user is authenticated
        # The first call to _getRemoteClusters comes from self._account.loginStateChanged
        if not self.update_timer.isActive():
            self.update_timer.start()

    ##  Callback for when the request for getting the clusters. is finished.
    def _onGetRemoteClustersFinished(self, clusters: List[CloudCluster]) -> None:
        found_clusters = {c.cluster_id: c for c in clusters}

        Logger.log("i", "Parsed remote clusters to %s", found_clusters)

        known_cluster_ids = set(self._remote_clusters.keys())
        found_cluster_ids = set(found_clusters.keys())

        # Add an output device for each new remote cluster.
        # We only add when is_online as we don't want the option in the drop down if the cluster is not online.
        for cluster_id in found_cluster_ids.difference(known_cluster_ids):
            if found_clusters[cluster_id].is_online:
                self._addCloudOutputDevice(found_clusters[cluster_id])

        # Remove output devices that are gone
        for cluster_id in known_cluster_ids.difference(found_cluster_ids):
            self._removeCloudOutputDevice(found_clusters[cluster_id])

        # TODO: not pass clusters that are not online?
        self._connectToActiveMachine(clusters)

    ##  Adds a CloudOutputDevice for each entry in the remote cluster list from the API.
    #   \param cluster: The cluster that was added.
    def _addCloudOutputDevice(self, cluster: CloudCluster):
        device = CloudOutputDevice(self._api, cluster.cluster_id)
        self._output_device_manager.addOutputDevice(device)
        self._remote_clusters[cluster.cluster_id] = device

    ##  Remove a CloudOutputDevice
    #   \param cluster: The cluster that was removed
    def _removeCloudOutputDevice(self, cluster: CloudCluster):
        self._output_device_manager.removeOutputDevice(cluster.cluster_id)
        if cluster.cluster_id in self._remote_clusters:
            del self._remote_clusters[cluster.cluster_id]

    ##  Callback for when the active machine was changed by the user or a new remote cluster was found.
    def _connectToActiveMachine(self, clusters: List[CloudCluster]) -> None:
        active_machine = CuraApplication.getInstance().getGlobalContainerStack()
        if not active_machine:
            return

        # Check if the stored cluster_id for the active machine is in our list of remote clusters.
        stored_cluster_id = active_machine.getMetaDataEntry("um_cloud_cluster_id")
        if stored_cluster_id in self._remote_clusters.keys():
            return self._remote_clusters.get(stored_cluster_id).connect()

        # Check if the active printer has a local network connection and match this key to the remote cluster.
        # The local network key is formatted as ultimakersystem-xxxxxxxxxxxx._ultimaker._tcp.local.
        # The optional remote host_name is formatted as ultimakersystem-xxxxxxxxxxxx.
        # This means we can match the two by checking if the host_name is in the network key string.

        local_network_key = active_machine.getMetaDataEntry("um_network_key")
        if not local_network_key:
            return

        cluster_id = next(local_network_key in cluster.host_name for cluster in clusters)
        if cluster_id in self._remote_clusters.keys():
            return self._remote_clusters.get(cluster_id).connect()

    ## Handles an API error received from the cloud.
    #  \param errors: The errors received
    def _onApiError(self, errors: List[CloudErrorObject]) -> None:
        message = ". ".join(e.title for e in errors)  # TODO: translate errors
        message = Message(
            text = message,
            title = self.I18N_CATALOG.i18nc("@info:title", "Error"),
            lifetime = 10,
            dismissable = True
        )
        message.show()
