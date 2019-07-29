# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Dict, List

from PyQt5.QtCore import QTimer

from UM import i18nCatalog
from UM.Logger import Logger
from UM.Signal import Signal
from cura.API import Account
from cura.CuraApplication import CuraApplication
from cura.Settings.GlobalStack import GlobalStack

from .CloudApiClient import CloudApiClient
from .CloudOutputDevice import CloudOutputDevice
from ..Models.Http.CloudClusterResponse import CloudClusterResponse
from ..Models.Http.CloudError import CloudError


##  The cloud output device manager is responsible for using the Ultimaker Cloud APIs to manage remote clusters.
#   Keeping all cloud related logic in this class instead of the UM3OutputDevicePlugin results in more readable code.
#
#   API spec is available on https://api.ultimaker.com/docs/connect/spec/.
#
class CloudOutputDeviceManager:

    META_CLUSTER_ID = "um_cloud_cluster_id"

    # The interval with which the remote clusters are checked
    CHECK_CLUSTER_INTERVAL = 30.0  # seconds

    # The translation catalog for this device.
    I18N_CATALOG = i18nCatalog("cura")

    # Signal emitted when the list of discovered devices changed.
    discoveredDevicesChanged = Signal()

    def __init__(self) -> None:
        # Persistent dict containing the remote clusters for the authenticated user.
        self._remote_clusters = {}  # type: Dict[str, CloudOutputDevice]
        self._account = CuraApplication.getInstance().getCuraAPI().account  # type: Account
        self._api = CloudApiClient(self._account, self._onApiError)

        # Create a timer to update the remote cluster list
        self._update_timer = QTimer()
        self._update_timer.setInterval(int(self.CHECK_CLUSTER_INTERVAL * 1000))
        self._update_timer.setSingleShot(False)

        # Ensure we don't start twice.
        self._running = False

    ## Starts running the cloud output device manager, thus periodically requesting cloud data.
    def start(self):
        if self._running:
            return
        self._account.loginStateChanged.connect(self._onLoginStateChanged)
        self._update_timer.timeout.connect(self._getRemoteClusters)
        self._onLoginStateChanged(is_logged_in=self._account.isLoggedIn)

    ## Stops running the cloud output device manager.
    def stop(self):
        if not self._running:
            return
        self._account.loginStateChanged.disconnect(self._onLoginStateChanged)
        self._update_timer.timeout.disconnect(self._getRemoteClusters)
        self._onLoginStateChanged(is_logged_in=False)

    ## Force refreshing connections.
    def refreshConnections(self) -> None:
        self._connectToActiveMachine()

    ## Called when the uses logs in or out
    def _onLoginStateChanged(self, is_logged_in: bool) -> None:
        if is_logged_in:
            if not self._update_timer.isActive():
                self._update_timer.start()
            self._getRemoteClusters()
        else:
            if self._update_timer.isActive():
                self._update_timer.stop()
            # Notify that all clusters have disappeared
            self._onGetRemoteClustersFinished([])

    ## Gets all remote clusters from the API.
    def _getRemoteClusters(self) -> None:
        self._api.getClusters(self._onGetRemoteClustersFinished)

    ## Callback for when the request for getting the clusters is finished.
    def _onGetRemoteClustersFinished(self, clusters: List[CloudClusterResponse]) -> None:

        # Filter on clusters that are currently online.
        online_clusters = {c.cluster_id: c for c in clusters if c.is_online}  # type: Dict[str, CloudClusterResponse]

        # Keep track of the new cloud clusters to show.
        # We create a new list instead of changing the existing one to prevent issues with ordering.
        new_devices = {}  # type: Dict[str, CloudOutputDevice]

        # Get the discovery mechanism of Cura.
        discovery = CuraApplication.getInstance().getDiscoveredPrintersModel()

        # Check which devices need to be created or updated.
        for device_id, cluster_data in online_clusters.items():
            device = next(iter(device for device in self._remote_clusters.values() if device.key == device_id), None)
            if not device:
                device = CloudOutputDevice(self._api, cluster_data)
                discovery.addDiscoveredPrinter(device.key, device.key, cluster_data.friendly_name,
                                               self._createMachineFromDiscoveredPrinter, device.printerType, device)
            else:
                discovery.updateDiscoveredPrinter(device.key, cluster_data.friendly_name, device.printerType)
            new_devices[device.key] = device

        # Remove output devices that disappeared.
        remote_cluster_keys = self._remote_clusters.keys()
        removed_devices = [cluster for cluster in self._remote_clusters.values() if cluster.key not in remote_cluster_keys]
        for device in removed_devices:
            CuraApplication.getInstance().getOutputDeviceManager().removeOutputDevice(device.key)
            discovery.removeDiscoveredPrinter(device.key)

        self._remote_clusters = new_devices
        self.discoveredDevicesChanged.emit()
        self._connectToActiveMachine()

    def _createMachineFromDiscoveredPrinter(self, key: str) -> None:
        device = self._remote_clusters[key]  # type: CloudOutputDevice
        if not device:
            Logger.log("e", "Could not find discovered device with key [%s]", key)
            return

        group_name = device.clusterData.friendly_name
        machine_type_id = device.printerType

        Logger.log("i", "Creating machine from cloud device with key = [%s], group name = [%s],  printer type = [%s]",
                   key, group_name, machine_type_id)

        # The newly added machine is automatically activated.
        CuraApplication.getInstance().getMachineManager().addMachine(machine_type_id, group_name)
        self._connectToActiveMachine()

    ##  Callback for when the active machine was changed by the user or a new remote cluster was found.
    def _connectToActiveMachine(self) -> None:
        active_machine = CuraApplication.getInstance().getGlobalContainerStack()
        if not active_machine:
            return

        # Remove all output devices that we have registered.
        # This is needed because when we switch we can only leave output devices that are meant for that machine.
        for device_id in self._remote_clusters:
            CuraApplication.getInstance().getOutputDeviceManager().removeOutputDevice(device_id)

        # Check if the stored cluster_id for the active machine is in our list of remote clusters.
        stored_cluster_id = active_machine.getMetaDataEntry(self.META_CLUSTER_ID)
        if stored_cluster_id in self._remote_clusters:
            device = self._remote_clusters[stored_cluster_id]
            self._connectToOutputDevice(device, active_machine)
            Logger.log("d", "Device connected by metadata cluster ID %s", stored_cluster_id)
        else:
            self._connectByNetworkKey(active_machine)

    ## Tries to match the local network key to the cloud cluster host name.
    def _connectByNetworkKey(self, active_machine: GlobalStack) -> None:
        # Check if the active printer has a local network connection and match this key to the remote cluster.
        local_network_key = active_machine.getMetaDataEntry("um_network_key")
        if not local_network_key:
            return

        device = next((c for c in self._remote_clusters.values() if c.matchesNetworkKey(local_network_key)), None)
        if not device:
            return

        Logger.log("i", "Found cluster %s with network key %s", device, local_network_key)
        active_machine.setMetaDataEntry(self.META_CLUSTER_ID, device.key)
        self._connectToOutputDevice(device, active_machine)

    ## Connects to an output device and makes sure it is registered in the output device manager.
    def _connectToOutputDevice(self, device: CloudOutputDevice, active_machine: GlobalStack) -> None:
        device.connect()
        active_machine.setMetaDataEntry(self.META_CLUSTER_ID, device.key)
        active_machine.addConfiguredConnectionType(device.connectionType.value)
        CuraApplication.getInstance().getOutputDeviceManager().addOutputDevice(device)

    ## Handles an API error received from the cloud.
    #  \param errors: The errors received
    @staticmethod
    def _onApiError(errors: List[CloudError] = None) -> None:
        for error in errors:
            Logger.log("w", str(error.toDict()))
