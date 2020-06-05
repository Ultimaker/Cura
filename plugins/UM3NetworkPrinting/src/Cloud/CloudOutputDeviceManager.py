# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import os
from typing import Dict, List, Optional, Set

from PyQt5.QtCore import QTimer
from PyQt5.QtNetwork import QNetworkReply

from UM import i18nCatalog
from UM.Logger import Logger  # To log errors talking to the API.
from UM.Message import Message
from UM.Settings.Interfaces import ContainerInterface
from UM.Signal import Signal
from UM.Util import parseBool
from cura.API import Account
from cura.API.Account import SyncState
from cura.CuraApplication import CuraApplication
from cura.Settings.CuraStackBuilder import CuraStackBuilder
from cura.Settings.GlobalStack import GlobalStack
from .CloudApiClient import CloudApiClient
from .CloudOutputDevice import CloudOutputDevice
from ..Models.Http.CloudClusterResponse import CloudClusterResponse


class CloudOutputDeviceManager:
    """The cloud output device manager is responsible for using the Ultimaker Cloud APIs to manage remote clusters.

    Keeping all cloud related logic in this class instead of the UM3OutputDevicePlugin results in more readable code.
    API spec is available on https://api.ultimaker.com/docs/connect/spec/.
    """

    META_CLUSTER_ID = "um_cloud_cluster_id"
    META_NETWORK_KEY = "um_network_key"
    SYNC_SERVICE_NAME = "CloudOutputDeviceManager"
    META_LINKED_TO_ACCOUNT = "linked_to_account"

    # The translation catalog for this device.
    I18N_CATALOG = i18nCatalog("cura")

    # Signal emitted when the list of discovered devices changed.
    discoveredDevicesChanged = Signal()

    def __init__(self) -> None:
        # Persistent dict containing the remote clusters for the authenticated user.
        self._remote_clusters = {}  # type: Dict[str, CloudOutputDevice]

        # Dictionary containing all the cloud printers loaded in Cura
        self._um_cloud_printers = {}  # type: Dict[str, GlobalStack]

        self._account = CuraApplication.getInstance().getCuraAPI().account  # type: Account
        self._api = CloudApiClient(CuraApplication.getInstance(), on_error = lambda error: Logger.log("e", str(error)))
        self._account.loginStateChanged.connect(self._onLoginStateChanged)

        # Ensure we don't start twice.
        self._running = False

        self._syncing = False

        CuraApplication.getInstance().getContainerRegistry().containerRemoved.connect(self._printerRemoved)

    def start(self):
        """Starts running the cloud output device manager, thus periodically requesting cloud data."""

        if self._running:
            return
        if not self._account.isLoggedIn:
            return
        self._running = True
        self._getRemoteClusters()

        self._account.syncRequested.connect(self._getRemoteClusters)

    def stop(self):
        """Stops running the cloud output device manager."""

        if not self._running:
            return
        self._running = False
        self._onGetRemoteClustersFinished([])  # Make sure we remove all cloud output devices.

    def refreshConnections(self) -> None:
        """Force refreshing connections."""

        self._connectToActiveMachine()

    def _onLoginStateChanged(self, is_logged_in: bool) -> None:
        """Called when the uses logs in or out"""

        if is_logged_in:
            self.start()
        else:
            self.stop()

    def _getRemoteClusters(self) -> None:
        """Gets all remote clusters from the API."""

        if self._syncing:
            return

        Logger.info("Syncing cloud printer clusters")

        self._syncing = True
        self._account.setSyncState(self.SYNC_SERVICE_NAME, SyncState.SYNCING)
        self._api.getClusters(self._onGetRemoteClustersFinished, self._onGetRemoteClusterFailed)

    def _onGetRemoteClustersFinished(self, clusters: List[CloudClusterResponse]) -> None:
        """Callback for when the request for getting the clusters is finished."""

        self._um_cloud_printers = {m.getMetaDataEntry(self.META_CLUSTER_ID): m for m in
                                   CuraApplication.getInstance().getContainerRegistry().findContainerStacks(
                                       type = "machine") if m.getMetaDataEntry(self.META_CLUSTER_ID, None)}
        new_clusters = []
        all_clusters = {c.cluster_id: c for c in clusters}  # type: Dict[str, CloudClusterResponse]
        online_clusters = {c.cluster_id: c for c in clusters if c.is_online}  # type: Dict[str, CloudClusterResponse]

        # Add the new printers in Cura. If a printer was previously added and is rediscovered, set its metadata to
        # reflect that and mark the printer not removed from the account
        for device_id, cluster_data in all_clusters.items():
            if device_id not in self._remote_clusters:
                new_clusters.append(cluster_data)
            if device_id in self._um_cloud_printers and not parseBool(self._um_cloud_printers[device_id].getMetaDataEntry(self.META_LINKED_TO_ACCOUNT, "true")):
                self._um_cloud_printers[device_id].setMetaDataEntry(self.META_LINKED_TO_ACCOUNT, True)
        self._onDevicesDiscovered(new_clusters)

        # Remove the CloudOutput device for offline printers
        offline_device_keys = set(self._remote_clusters.keys()) - set(online_clusters.keys())
        for device_id in offline_device_keys:
            self._onDiscoveredDeviceRemoved(device_id)

        # Handle devices that were previously added in Cura but do not exist in the account anymore (i.e. they were
        # removed from the account)
        removed_device_keys = set(self._um_cloud_printers.keys()) - set(all_clusters.keys())
        if removed_device_keys:
            self._devicesRemovedFromAccount(removed_device_keys)

        if new_clusters or offline_device_keys or removed_device_keys:
            self.discoveredDevicesChanged.emit()
        if offline_device_keys:
            # If the removed device was active we should connect to the new active device
            self._connectToActiveMachine()

        self._syncing = False
        self._account.setSyncState(self.SYNC_SERVICE_NAME, SyncState.SUCCESS)

    def _onGetRemoteClusterFailed(self, reply: QNetworkReply, error: QNetworkReply.NetworkError) -> None:
        self._syncing = False
        self._account.setSyncState(self.SYNC_SERVICE_NAME, SyncState.ERROR)

    def _onDevicesDiscovered(self, clusters: List[CloudClusterResponse]) -> None:
        """**Synchronously** create machines for discovered devices

        Any new machines are made available to the user.
        May take a long time to complete. As this code needs access to the Application
        and blocks the GIL, creating a Job for this would not make sense.
        Shows a Message informing the user of progress.
        """
        new_devices = []
        remote_clusters_added = False
        for cluster_data in clusters:
            device = CloudOutputDevice(self._api, cluster_data)
            # Create a machine if we don't already have it. Do not make it the active machine.
            machine_manager = CuraApplication.getInstance().getMachineManager()

            # We only need to add it if it wasn't already added by "local" network or by cloud.
            if machine_manager.getMachine(device.printerType, {self.META_CLUSTER_ID: device.key}) is None \
                    and machine_manager.getMachine(device.printerType, {self.META_NETWORK_KEY: cluster_data.host_name + "*"}) is None:  # The host name is part of the network key.
                new_devices.append(device)
            elif device.getId() not in self._remote_clusters:
                self._remote_clusters[device.getId()] = device
                remote_clusters_added = True
            # If a printer that was removed from the account is re-added, change its metadata to mark it not removed
            # from the account
            elif not parseBool(self._um_cloud_printers[device.key].getMetaDataEntry(self.META_LINKED_TO_ACCOUNT, "true")):
                self._um_cloud_printers[device.key].setMetaDataEntry(self.META_LINKED_TO_ACCOUNT, True)

        # Inform the Cloud printers model about new devices.
        new_devices_list_of_dicts = [{
                "key": d.getId(),
                "name": d.name,
                "machine_type": d.printerTypeName,
                "firmware_version": d.firmwareVersion} for d in new_devices]
        discovered_cloud_printers_model = CuraApplication.getInstance().getDiscoveredCloudPrintersModel()
        discovered_cloud_printers_model.addDiscoveredCloudPrinters(new_devices_list_of_dicts)

        if not new_devices:
            if remote_clusters_added:
                self._connectToActiveMachine()
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

            # If there is no active machine, activate the first available cloud printer
            activate = not CuraApplication.getInstance().getMachineManager().activeMachine
            self._createMachineFromDiscoveredDevice(device.getId(), activate = activate)

        message.setProgress(None)

        max_disp_devices = 3
        if len(new_devices) > max_disp_devices:
            num_hidden = len(new_devices) - max_disp_devices + 1
            device_name_list = ["<li>{} ({})</li>".format(device.name, device.printerTypeName) for device in new_devices[0:num_hidden]]
            device_name_list.append(self.I18N_CATALOG.i18nc("info:hidden list items", "<li>... and {} others</li>", num_hidden))
            device_names = "\n".join(device_name_list)
        else:
            device_names = "\n".join(["<li>{} ({})</li>".format(device.name, device.printerTypeName) for device in new_devices])

        message_text = self.I18N_CATALOG.i18nc(
            "info:status",
            "Cloud printers added from your account:\n<ul>{}</ul>",
            device_names
        )
        message.setText(message_text)

    def _devicesRemovedFromAccount(self, removed_device_ids: Set[str]) -> None:
        """
        Removes the CloudOutputDevice from the received device ids and marks the specific printers as "removed from
        account". In addition, it generates a message to inform the user about the printers that are no longer linked to
        his/her account. The message is not generated if all the printers have been previously reported as not linked
        to the account.

        :param removed_device_ids: Set of device ids, whose CloudOutputDevice needs to be removed
        :return: None
        """

        if not CuraApplication.getInstance().getCuraAPI().account.isLoggedIn:
            return

        # Do not report device ids which have been previously marked as non-linked to the account
        ignored_device_ids = set()
        for device_id in removed_device_ids:
            if not parseBool(self._um_cloud_printers[device_id].getMetaDataEntry(self.META_LINKED_TO_ACCOUNT, "true")):
                ignored_device_ids.add(device_id)
        # Keep the reported_device_ids list in a class variable, so that the message button actions can access it and
        # take the necessary steps to fulfill their purpose.
        self.reported_device_ids = removed_device_ids - ignored_device_ids
        if len(self.reported_device_ids) == 0:
            return

        # Generate message
        removed_printers_message = Message(
                title = self.I18N_CATALOG.i18ncp(
                        "info:status",
                        "Cloud connection is not available for a printer",
                        "Cloud connection is not available for some printers",
                        len(self.reported_device_ids)
                ),
                lifetime = 0
        )
        device_names = "\n".join(["<li>{} ({})</li>".format(self._um_cloud_printers[device].name, self._um_cloud_printers[device].definition.name) for device in self.reported_device_ids])
        message_text = self.I18N_CATALOG.i18ncp(
                "info:status",
                "The following cloud printer is not linked to your account:\n",
                "The following cloud printers are not linked to your account:\n",
                len(self.reported_device_ids)
        )
        message_text += self.I18N_CATALOG.i18nc(
                "info:status",
                "<ul>{}</ul>\nTo establish a connection, please visit the "
                "<a href='https://mycloud.ultimaker.com/'>Ultimaker Digital Factory</a>.",
                device_names
        )
        removed_printers_message.setText(message_text)

        # Remove the output device from the printers
        for device_id in removed_device_ids:
            device = self._um_cloud_printers.get(device_id, None)  # type: Optional[GlobalStack]
            if not device:
                continue
            output_device_manager = CuraApplication.getInstance().getOutputDeviceManager()
            if device_id in output_device_manager.getOutputDeviceIds():
                output_device_manager.removeOutputDevice(device_id)
            if device_id in self._remote_clusters:
                del self._remote_clusters[device_id]

            # Update the printer's metadata to mark it as not linked to the account
            device.setMetaDataEntry(self.META_LINKED_TO_ACCOUNT, False)

        removed_printers_message.show()

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

        self._setOutputDeviceMetadata(device, new_machine)

        if activate:
            CuraApplication.getInstance().getMachineManager().setActiveMachine(new_machine.getId())

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

    def _setOutputDeviceMetadata(self, device: CloudOutputDevice, machine: GlobalStack):
        machine.setName(device.name)
        machine.setMetaDataEntry(self.META_CLUSTER_ID, device.key)
        machine.setMetaDataEntry("group_name", device.name)
        machine.setMetaDataEntry("removal_warning", self.I18N_CATALOG.i18nc(
            "@label ({} is printer name)",
            "{} will be removed until the next account sync. <br> To remove {} permanently, "
            "visit <a href='https://mycloud.ultimaker.com/'>Ultimaker Digital Factory</a>. "
            "<br><br>Are you sure you want to remove {} temporarily?",
            device.name, device.name, device.name
        ))
        machine.addConfiguredConnectionType(device.connectionType.value)

    def _connectToOutputDevice(self, device: CloudOutputDevice, machine: GlobalStack) -> None:
        """Connects to an output device and makes sure it is registered in the output device manager."""

        self._setOutputDeviceMetadata(device, machine)

        if not device.isConnected():
            device.connect()

        output_device_manager = CuraApplication.getInstance().getOutputDeviceManager()
        if device.key not in output_device_manager.getOutputDeviceIds():
            output_device_manager.addOutputDevice(device)

    def _printerRemoved(self, container: ContainerInterface) -> None:
        """
        Callback connected to the containerRemoved signal. Invoked when a cloud printer is removed from Cura to remove
        the printer's reference from the _remote_clusters.

        :param container: The ContainerInterface passed to this function whenever the ContainerRemoved signal is emitted
        :return: None
        """
        if isinstance(container, GlobalStack):
            container_cluster_id = container.getMetaDataEntry(self.META_CLUSTER_ID, None)
            if container_cluster_id in self._remote_clusters.keys():
                del self._remote_clusters[container_cluster_id]
