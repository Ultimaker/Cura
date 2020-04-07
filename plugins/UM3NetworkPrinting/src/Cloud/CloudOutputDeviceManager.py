# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import os
from typing import Dict, List, Optional

from PyQt5.QtCore import QTimer

from UM import i18nCatalog
from UM.Logger import Logger  # To log errors talking to the API.
from UM.Message import Message
from UM.Signal import Signal
from cura.API import Account
from cura.CuraApplication import CuraApplication
from cura.Settings.CuraStackBuilder import CuraStackBuilder
from cura.Settings.GlobalStack import GlobalStack
from .CloudApiClient import CloudApiClient
from .CloudOutputDevice import CloudOutputDevice
from ..Models.Http.CloudClusterResponse import CloudClusterResponse


## The cloud output device manager is responsible for using the Ultimaker Cloud APIs to manage remote clusters.
#  Keeping all cloud related logic in this class instead of the UM3OutputDevicePlugin results in more readable code.
#  API spec is available on https://api.ultimaker.com/docs/connect/spec/.
class CloudOutputDeviceManager:

    META_CLUSTER_ID = "um_cloud_cluster_id"
    META_NETWORK_KEY = "um_network_key"

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
        self._api = CloudApiClient(self._account, on_error = lambda error: Logger.log("e", str(error)))
        self._account.loginStateChanged.connect(self._onLoginStateChanged)

        # Create a timer to update the remote cluster list
        self._update_timer = QTimer()
        self._update_timer.setInterval(int(self.CHECK_CLUSTER_INTERVAL * 1000))
        self._update_timer.setSingleShot(False)
        self._update_timer.timeout.connect(self._getRemoteClusters)

        # Ensure we don't start twice.
        self._running = False

    ## Starts running the cloud output device manager, thus periodically requesting cloud data.
    def start(self):
        if self._running:
            return
        if not self._account.isLoggedIn:
            return
        self._running = True
        if not self._update_timer.isActive():
            self._update_timer.start()
        self._getRemoteClusters()

    ## Stops running the cloud output device manager.
    def stop(self):
        if not self._running:
            return
        self._running = False
        if self._update_timer.isActive():
            self._update_timer.stop()
        self._onGetRemoteClustersFinished([])  # Make sure we remove all cloud output devices.

    ## Force refreshing connections.
    def refreshConnections(self) -> None:
        self._connectToActiveMachine()

    ## Called when the uses logs in or out
    def _onLoginStateChanged(self, is_logged_in: bool) -> None:
        if is_logged_in:
            self.start()
        else:
            self.stop()

    ## Gets all remote clusters from the API.
    def _getRemoteClusters(self) -> None:
        self._api.getClusters(self._onGetRemoteClustersFinished)

    ## Callback for when the request for getting the clusters is finished.
    def _onGetRemoteClustersFinished(self, clusters: List[CloudClusterResponse]) -> None:
        new_clusters = []
        online_clusters = {c.cluster_id: c for c in clusters if c.is_online}  # type: Dict[str, CloudClusterResponse]
        for device_id, cluster_data in online_clusters.items():
            if device_id not in self._remote_clusters:
                new_clusters.append(cluster_data)
            else:
                self._onDiscoveredDeviceUpdated(cluster_data)

        self._onDevicesDiscovered(new_clusters)

        removed_device_keys = set(self._remote_clusters.keys()) - set(online_clusters.keys())
        for device_id in removed_device_keys:
            self._onDiscoveredDeviceRemoved(device_id)

        if new_clusters or removed_device_keys:
            self.discoveredDevicesChanged.emit()
        if removed_device_keys:
            # If the removed device was active we should connect to the new active device
            self._connectToActiveMachine()

    def _onDevicesDiscovered(self, clusters: List[CloudClusterResponse]) -> None:
        """**Synchronously** create machines for discovered devices

        Any new machines are made available to the user.
        May take a long time to complete. As this code needs access to the Application
        and blocks the GIL, creating a Job for this would not make sense.
        Shows a Message informing the user of progress.
        """
        new_devices = []
        for cluster_data in clusters:
            device = CloudOutputDevice(self._api, cluster_data)
            # Create a machine if we don't already have it. Do not make it the active machine.
            meta_data = {self.META_CLUSTER_ID: device.key}
            if CuraApplication.getInstance().getMachineManager().getMachine(device.printerType, meta_data) is None:
                new_devices.append(device)

        if not new_devices:
            return

        new_devices.sort(key = lambda x: x.name.lower())

        image_path = os.path.join(
            CuraApplication.getInstance().getPluginRegistry().getPluginPath("UM3NetworkPrinting") or "",
            "resources", "svg", "cloud-flow-completed.svg"
        )

        message = Message(
            title = self.I18N_CATALOG.i18ncp(
                "info:status",
                "New printer detected from your Ultimaker account",
                "New printers detected from your Ultimaker account",
                len(new_devices)
            ),
            progress = 0,
            lifetime = 0,
            image_source = image_path
        )
        message.show()

        for idx, device in enumerate(new_devices):
            message_text = self.I18N_CATALOG.i18nc(
                "info:status", "Adding printer {} ({}) from your account",
                device.name,
                device.printerTypeName
            )
            message.setText(message_text)
            if len(new_devices) > 1:
                message.setProgress((idx / len(new_devices)) * 100)
            CuraApplication.getInstance().processEvents()
            self._remote_clusters[device.getId()] = device
            self._createMachineFromDiscoveredDevice(device.getId(), activate = False)

        message.setProgress(None)

        max_disp_devices = 3
        if len(new_devices) > max_disp_devices:
            num_hidden = len(new_devices) - max_disp_devices + 1
            device_name_list = ["- {} ({})".format(device.name, device.printerTypeName) for device in new_devices[0:num_hidden]]
            device_name_list.append(self.I18N_CATALOG.i18nc("info:hidden list items", "- and {} others", num_hidden))
            device_names = "\n".join(device_name_list)
        else:
            device_names = "\n".join(["- {} ({})".format(device.name, device.printerTypeName) for device in new_devices])

        message_text = self.I18N_CATALOG.i18nc(
            "info:status",
            "Cloud printers added from your account:\n{}",
            device_names
        )
        message.setText(message_text)

    def _onDiscoveredDeviceUpdated(self, cluster_data: CloudClusterResponse) -> None:
        device = self._remote_clusters.get(cluster_data.cluster_id)
        if not device:
            return
        CuraApplication.getInstance().getDiscoveredPrintersModel().updateDiscoveredPrinter(
            ip_address=device.key,
            name=cluster_data.friendly_name,
            machine_type=device.printerType
        )
        self.discoveredDevicesChanged.emit()

    def _onDiscoveredDeviceRemoved(self, device_id: str) -> None:
        device = self._remote_clusters.pop(device_id, None)  # type: Optional[CloudOutputDevice]
        if not device:
            return
        device.close()
        output_device_manager = CuraApplication.getInstance().getOutputDeviceManager()
        if device.key in output_device_manager.getOutputDeviceIds():
            output_device_manager.removeOutputDevice(device.key)

    def _createMachineFromDiscoveredDevice(self, key: str, activate: bool = True) -> None:
        device = self._remote_clusters[key]
        if not device:
            return

        # Create a new machine.
        # We do not use use MachineManager.addMachine here because we need to set the cluster ID before activating it.
        new_machine = CuraStackBuilder.createMachine(device.name, device.printerType)
        if not new_machine:
            Logger.log("e", "Failed creating a new machine")
            return
        new_machine.setMetaDataEntry(self.META_CLUSTER_ID, device.key)

        if activate:
            CuraApplication.getInstance().getMachineManager().setActiveMachine(new_machine.getId())

        self._connectToOutputDevice(device, new_machine)

    def _connectToActiveMachine(self) -> None:
        """Callback for when the active machine was changed by the user"""

        active_machine = CuraApplication.getInstance().getGlobalContainerStack()
        if not active_machine:
            return

        output_device_manager = CuraApplication.getInstance().getOutputDeviceManager()
        stored_cluster_id = active_machine.getMetaDataEntry(self.META_CLUSTER_ID)
        local_network_key = active_machine.getMetaDataEntry(self.META_NETWORK_KEY)
        for device in self._remote_clusters.values():
            if device.key == stored_cluster_id:
                # Connect to it if the stored ID matches.
                self._connectToOutputDevice(device, active_machine)
            elif local_network_key and device.matchesNetworkKey(local_network_key):
                # Connect to it if we can match the local network key that was already present.
                self._connectToOutputDevice(device, active_machine)
            elif device.key in output_device_manager.getOutputDeviceIds():
                # Remove device if it is not meant for the active machine.
                output_device_manager.removeOutputDevice(device.key)

    ## Connects to an output device and makes sure it is registered in the output device manager.
    def _connectToOutputDevice(self, device: CloudOutputDevice, machine: GlobalStack) -> None:
        machine.setName(device.name)
        machine.setMetaDataEntry(self.META_CLUSTER_ID, device.key)
        machine.setMetaDataEntry("group_name", device.name)
        machine.addConfiguredConnectionType(device.connectionType.value)

        if not device.isConnected():
            device.connect()

        output_device_manager = CuraApplication.getInstance().getOutputDeviceManager()
        if device.key not in output_device_manager.getOutputDeviceIds():
            output_device_manager.addOutputDevice(device)