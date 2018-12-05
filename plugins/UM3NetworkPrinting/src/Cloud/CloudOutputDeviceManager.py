# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Dict, List

from PyQt5.QtCore import QTimer

from UM import i18nCatalog
from UM.Logger import Logger
from UM.Message import Message
from cura.CuraApplication import CuraApplication
from cura.Settings.GlobalStack import GlobalStack
from .CloudApiClient import CloudApiClient
from .CloudOutputDevice import CloudOutputDevice
from .Models.CloudCluster import CloudCluster
from .Models.CloudErrorObject import CloudErrorObject
from .Utils import findChanges


##  The cloud output device manager is responsible for using the Ultimaker Cloud APIs to manage remote clusters.
#   Keeping all cloud related logic in this class instead of the UM3OutputDevicePlugin results in more readable code.
#
#   API spec is available on https://api.ultimaker.com/docs/connect/spec/.
#

class CloudOutputDeviceManager:
    META_CLUSTER_ID = "um_cloud_cluster_id"

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

        # create a timer to update the remote cluster list
        self._update_timer = QTimer(application)
        self._update_timer.setInterval(self.CHECK_CLUSTER_INTERVAL * 1000)
        self._update_timer.setSingleShot(False)
        self._update_timer.timeout.connect(self._getRemoteClusters)

    ##  Gets all remote clusters from the API.
    def _getRemoteClusters(self) -> None:
        Logger.log("i", "Retrieving remote clusters")
        if self._account.isLoggedIn:
            self._api.getClusters(self._onGetRemoteClustersFinished)
            # Only start the polling timer after the user is authenticated
            # The first call to _getRemoteClusters comes from self._account.loginStateChanged
            if not self._update_timer.isActive():
                self._update_timer.start()
        else:
            self._onGetRemoteClustersFinished([])
            if self._update_timer.isActive():
                self._update_timer.stop()

    ##  Callback for when the request for getting the clusters. is finished.
    def _onGetRemoteClustersFinished(self, clusters: List[CloudCluster]) -> None:
        online_clusters = {c.cluster_id: c for c in clusters if c.is_online}  # type: Dict[str, CloudCluster]

        removed_devices, added_clusters, updates = findChanges(self._remote_clusters, online_clusters)

        Logger.log("i", "Parsed remote clusters to %s", online_clusters)

        # Remove output devices that are gone
        for removed_cluster in removed_devices:
            if removed_cluster.isConnected():
                removed_cluster.disconnect()
            self._output_device_manager.removeOutputDevice(removed_cluster.key)
            del self._remote_clusters[removed_cluster.key]

        # Add an output device for each new remote cluster.
        # We only add when is_online as we don't want the option in the drop down if the cluster is not online.
        for added_cluster in added_clusters:
            device = CloudOutputDevice(self._api, added_cluster.cluster_id, added_cluster.host_name)
            self._output_device_manager.addOutputDevice(device)
            self._remote_clusters[added_cluster.cluster_id] = device

        for device, cluster in updates:
            device.host_name = cluster.host_name

        self._connectToActiveMachine()

    ##  Callback for when the active machine was changed by the user or a new remote cluster was found.
    def _connectToActiveMachine(self) -> None:
        active_machine = CuraApplication.getInstance().getGlobalContainerStack()
        if not active_machine:
            return

        # Check if the stored cluster_id for the active machine is in our list of remote clusters.
        stored_cluster_id = active_machine.getMetaDataEntry(self.META_CLUSTER_ID)
        if stored_cluster_id in self._remote_clusters:
            device = self._remote_clusters[stored_cluster_id]
            if not device.isConnected():
                device.connect()
        else:
            self._connectByNetworkKey(active_machine)

    ##  Tries to match the
    def _connectByNetworkKey(self, active_machine: GlobalStack) -> None:
        # Check if the active printer has a local network connection and match this key to the remote cluster.
        local_network_key = active_machine.getMetaDataEntry("um_network_key")
        if not local_network_key:
            return

        device = next((c for c in self._remote_clusters.values() if c.matchesNetworkKey(local_network_key)), None)
        if not device:
            return

        active_machine.setMetaDataEntry(self.META_CLUSTER_ID, device.key)
        return device.connect()

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
