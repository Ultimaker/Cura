# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os
from typing import Dict, List, Optional, Set

from PyQt5.QtNetwork import QNetworkReply
from PyQt5.QtWidgets import QMessageBox

from UM import i18nCatalog
from UM.Logger import Logger  # To log errors talking to the API.
from UM.Message import Message
from UM.Settings.Interfaces import ContainerInterface
from UM.Signal import Signal
from UM.Util import parseBool
from cura.API import Account
from cura.API.Account import SyncState
from cura.CuraApplication import CuraApplication
from cura.Settings.CuraContainerRegistry import CuraContainerRegistry  # To update printer metadata with information received about cloud printers.
from cura.Settings.CuraStackBuilder import CuraStackBuilder
from cura.Settings.GlobalStack import GlobalStack
from cura.UltimakerCloud.UltimakerCloudConstants import META_UM_LINKED_TO_ACCOUNT
from .CloudApiClient import CloudApiClient
from .CloudOutputDevice import CloudOutputDevice
from ..Models.Http.CloudClusterResponse import CloudClusterResponse


class CloudOutputDeviceManager:
    """The cloud output device manager is responsible for using the Ultimaker Cloud APIs to manage remote clusters.

    Keeping all cloud related logic in this class instead of the UM3OutputDevicePlugin results in more readable code.
    API spec is available on https://api.ultimaker.com/docs/connect/spec/.
    """

    META_CLUSTER_ID = "um_cloud_cluster_id"
    META_HOST_GUID = "host_guid"
    META_NETWORK_KEY = "um_network_key"

    SYNC_SERVICE_NAME = "CloudOutputDeviceManager"

    # The translation catalog for this device.
    i18n_catalog = i18nCatalog("cura")

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
        self._removed_printers_message = None  # type: Optional[Message]

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

        self._syncing = True
        self._account.setSyncState(self.SYNC_SERVICE_NAME, SyncState.SYNCING)
        self._api.getClusters(self._onGetRemoteClustersFinished, self._onGetRemoteClusterFailed)

    def _onGetRemoteClustersFinished(self, clusters: List[CloudClusterResponse]) -> None:
        """Callback for when the request for getting the clusters is successful and finished."""

        self._um_cloud_printers = {m.getMetaDataEntry(self.META_CLUSTER_ID): m for m in
                                   CuraApplication.getInstance().getContainerRegistry().findContainerStacks(
                                       type = "machine") if m.getMetaDataEntry(self.META_CLUSTER_ID, None)}
        new_clusters = []
        all_clusters = {c.cluster_id: c for c in clusters}  # type: Dict[str, CloudClusterResponse]
        online_clusters = {c.cluster_id: c for c in clusters if c.is_online}  # type: Dict[str, CloudClusterResponse]

        # Add the new printers in Cura.
        for device_id, cluster_data in all_clusters.items():
            if device_id not in self._remote_clusters:
                new_clusters.append(cluster_data)
            if device_id in self._um_cloud_printers:
                # Existing cloud printers may not have the host_guid meta-data entry. If that's the case, add it.
                if not self._um_cloud_printers[device_id].getMetaDataEntry(self.META_HOST_GUID, None):
                    self._um_cloud_printers[device_id].setMetaDataEntry(self.META_HOST_GUID, cluster_data.host_guid)
                # If a printer was previously not linked to the account and is rediscovered, mark the printer as linked
                # to the current account
                if not parseBool(self._um_cloud_printers[device_id].getMetaDataEntry(META_UM_LINKED_TO_ACCOUNT, "true")):
                    self._um_cloud_printers[device_id].setMetaDataEntry(META_UM_LINKED_TO_ACCOUNT, True)
        self._onDevicesDiscovered(new_clusters)

        self._updateOnlinePrinters(all_clusters)

        # Hide the current removed_printers_message, if there is any
        if self._removed_printers_message:
            self._removed_printers_message.actionTriggered.disconnect(self._onRemovedPrintersMessageActionTriggered)
            self._removed_printers_message.hide()

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

        Logger.debug("Synced cloud printers with account.")

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
        host_guid_map = {machine.getMetaDataEntry(self.META_HOST_GUID): device_cluster_id
                         for device_cluster_id, machine in self._um_cloud_printers.items()
                         if machine.getMetaDataEntry(self.META_HOST_GUID)}
        machine_manager = CuraApplication.getInstance().getMachineManager()

        for cluster_data in clusters:
            device = CloudOutputDevice(self._api, cluster_data)
            # If the machine already existed before, it will be present in the host_guid_map
            if cluster_data.host_guid in host_guid_map:
                machine = machine_manager.getMachine(device.printerType, {self.META_HOST_GUID: cluster_data.host_guid})
                if machine and machine.getMetaDataEntry(self.META_CLUSTER_ID) != device.key:
                    # If the retrieved device has a different cluster_id than the existing machine, bring the existing
                    # machine up-to-date.
                    self._updateOutdatedMachine(outdated_machine = machine, new_cloud_output_device = device)

            # Create a machine if we don't already have it. Do not make it the active machine.
            # We only need to add it if it wasn't already added by "local" network or by cloud.
            if machine_manager.getMachine(device.printerType, {self.META_CLUSTER_ID: device.key}) is None \
                    and machine_manager.getMachine(device.printerType, {self.META_NETWORK_KEY: cluster_data.host_name + "*"}) is None:  # The host name is part of the network key.
                new_devices.append(device)
            elif device.getId() not in self._remote_clusters:
                self._remote_clusters[device.getId()] = device
                remote_clusters_added = True
            # If a printer that was removed from the account is re-added, change its metadata to mark it not removed
            # from the account
            elif not parseBool(self._um_cloud_printers[device.key].getMetaDataEntry(META_UM_LINKED_TO_ACCOUNT, "true")):
                self._um_cloud_printers[device.key].setMetaDataEntry(META_UM_LINKED_TO_ACCOUNT, True)

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

        # Sort new_devices on online status first, alphabetical second.
        # Since the first device might be activated in case there is no active printer yet,
        # it would be nice to prioritize online devices
        online_cluster_names = {c.friendly_name.lower() for c in clusters if c.is_online and not c.friendly_name is None}
        new_devices.sort(key = lambda x: ("a{}" if x.name.lower() in online_cluster_names else "b{}").format(x.name.lower()))

        message = Message(
            title = self.i18n_catalog.i18ncp(
                "info:status",
                "New printer detected from your Ultimaker account",
                "New printers detected from your Ultimaker account",
                len(new_devices)
            ),
            progress = 0,
            lifetime = 0,
            message_type = Message.MessageType.POSITIVE
        )
        message.show()

        for idx, device in enumerate(new_devices):
            message_text = self.i18n_catalog.i18nc("info:status Filled in with printer name and printer model.", "Adding printer {name} ({model}) from your account").format(name = device.name, model = device.printerTypeName)
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
            num_hidden = len(new_devices) - max_disp_devices
            device_name_list = ["<li>{} ({})</li>".format(device.name, device.printerTypeName) for device in new_devices[0:max_disp_devices]]
            device_name_list.append("<li>" + self.i18n_catalog.i18ncp("info:{0} gets replaced by a number of printers", "... and {0} other", "... and {0} others", num_hidden) + "</li>")
            device_names = "".join(device_name_list)
        else:
            device_names = "".join(["<li>{} ({})</li>".format(device.name, device.printerTypeName) for device in new_devices])

        message_text = self.i18n_catalog.i18nc("info:status", "Printers added from Digital Factory:") + "<ul>" + device_names + "</ul>"
        message.setText(message_text)

    def _updateOnlinePrinters(self, printer_responses: Dict[str, CloudClusterResponse]) -> None:
        """
        Update the metadata of the printers to store whether they are online or not.
        :param printer_responses: The responses received from the API about the printer statuses.
        """
        for container_stack in CuraContainerRegistry.getInstance().findContainerStacks(type = "machine"):
            cluster_id = container_stack.getMetaDataEntry("um_cloud_cluster_id", "")
            if cluster_id in printer_responses:
                container_stack.setMetaDataEntry("is_online", printer_responses[cluster_id].is_online)

    def _updateOutdatedMachine(self, outdated_machine: GlobalStack, new_cloud_output_device: CloudOutputDevice) -> None:
        """
         Update the cloud metadata of a pre-existing machine that is rediscovered (e.g. if the printer was removed and
         re-added to the account) and delete the old CloudOutputDevice related to this machine.

        :param outdated_machine: The cloud machine that needs to be brought up-to-date with the new data received from
                                 the account
        :param new_cloud_output_device: The new CloudOutputDevice that should be linked to the pre-existing machine
        :return: None
        """
        old_cluster_id = outdated_machine.getMetaDataEntry(self.META_CLUSTER_ID)
        outdated_machine.setMetaDataEntry(self.META_CLUSTER_ID, new_cloud_output_device.key)
        outdated_machine.setMetaDataEntry(META_UM_LINKED_TO_ACCOUNT, True)
        # Cleanup the remainings of the old CloudOutputDevice(old_cluster_id)
        self._um_cloud_printers[new_cloud_output_device.key] = self._um_cloud_printers.pop(old_cluster_id)
        output_device_manager = CuraApplication.getInstance().getOutputDeviceManager()
        if old_cluster_id in output_device_manager.getOutputDeviceIds():
            output_device_manager.removeOutputDevice(old_cluster_id)
        if old_cluster_id in self._remote_clusters:
            # We need to close the device so that it stops checking for its status
            self._remote_clusters[old_cluster_id].close()
            del self._remote_clusters[old_cluster_id]
            self._remote_clusters[new_cloud_output_device.key] = new_cloud_output_device

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
            if not parseBool(self._um_cloud_printers[device_id].getMetaDataEntry(META_UM_LINKED_TO_ACCOUNT, "true")):
                ignored_device_ids.add(device_id)
        # Keep the reported_device_ids list in a class variable, so that the message button actions can access it and
        # take the necessary steps to fulfill their purpose.
        self.reported_device_ids = removed_device_ids - ignored_device_ids
        if not self.reported_device_ids:
            return

        # Generate message
        self._removed_printers_message = Message(
                title = self.i18n_catalog.i18ncp(
                        "info:status",
                        "A cloud connection is not available for a printer",
                        "A cloud connection is not available for some printers",
                        len(self.reported_device_ids)
                ),
            message_type = Message.MessageType.WARNING
        )
        device_names = "".join(["<li>{} ({})</li>".format(self._um_cloud_printers[device].name, self._um_cloud_printers[device].definition.name) for device in self.reported_device_ids])
        message_text = self.i18n_catalog.i18ncp(
                "info:status",
                "This printer is not linked to the Digital Factory:",
                "These printers are not linked to the Digital Factory:",
                len(self.reported_device_ids)
        )
        message_text += "<br/><ul>{}</ul><br/>".format(device_names)
        digital_factory_string = self.i18n_catalog.i18nc("info:name", "Ultimaker Digital Factory")

        message_text += self.i18n_catalog.i18nc(
                "info:status",
                "To establish a connection, please visit the {website_link}".format(website_link = "<a href='https://digitalfactory.ultimaker.com?utm_source=cura&utm_medium=software&utm_campaign=change-account-connect-printer'>{}</a>.".format(digital_factory_string))
        )
        self._removed_printers_message.setText(message_text)
        self._removed_printers_message.addAction("keep_printer_configurations_action",
                                                 name = self.i18n_catalog.i18nc("@action:button", "Keep printer configurations"),
                                                 icon = "",
                                                 description = "Keep cloud printers in Ultimaker Cura when not connected to your account.",
                                                 button_align = Message.ActionButtonAlignment.ALIGN_RIGHT)
        self._removed_printers_message.addAction("remove_printers_action",
                                                 name = self.i18n_catalog.i18nc("@action:button", "Remove printers"),
                                                 icon = "",
                                                 description = "Remove cloud printer(s) which aren't linked to your account.",
                                                 button_style = Message.ActionButtonStyle.SECONDARY,
                                                 button_align = Message.ActionButtonAlignment.ALIGN_LEFT)
        self._removed_printers_message.actionTriggered.connect(self._onRemovedPrintersMessageActionTriggered)

        output_device_manager = CuraApplication.getInstance().getOutputDeviceManager()

        # Remove the output device from the printers
        for device_id in removed_device_ids:
            device = self._um_cloud_printers.get(device_id, None)  # type: Optional[GlobalStack]
            if not device:
                continue
            if device_id in output_device_manager.getOutputDeviceIds():
                output_device_manager.removeOutputDevice(device_id)
            if device_id in self._remote_clusters:
                del self._remote_clusters[device_id]

            # Update the printer's metadata to mark it as not linked to the account
            device.setMetaDataEntry(META_UM_LINKED_TO_ACCOUNT, False)

        self._removed_printers_message.show()

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
        for device in list(self._remote_clusters.values()):  # Make a copy of the remote devices list, to prevent modifying the list while iterating, if a device gets added asynchronously.
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
        machine.setMetaDataEntry(self.META_HOST_GUID, device.clusterData.host_guid)
        machine.setMetaDataEntry("group_name", device.name)
        machine.setMetaDataEntry("group_size", device.clusterSize)
        digital_factory_string = self.i18n_catalog.i18nc("info:name", "Ultimaker Digital Factory")
        digital_factory_link = "<a href='https://digitalfactory.ultimaker.com?utm_source=cura&utm_medium=software&utm_campaign=change-account-remove-printer'>{digital_factory_string}</a>".format(digital_factory_string = digital_factory_string)
        removal_warning_string = self.i18n_catalog.i18nc("@message {printer_name} is replaced with the name of the printer", "{printer_name} will be removed until the next account sync.").format(printer_name = device.name) \
            + "<br>" + self.i18n_catalog.i18nc("@message {printer_name} is replaced with the name of the printer", "To remove {printer_name} permanently, visit {digital_factory_link}").format(printer_name = device.name, digital_factory_link = digital_factory_link) \
            + "<br><br>" + self.i18n_catalog.i18nc("@message {printer_name} is replaced with the name of the printer", "Are you sure you want to remove {printer_name} temporarily?").format(printer_name = device.name)
        machine.setMetaDataEntry("removal_warning", removal_warning_string)
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

    def _onRemovedPrintersMessageActionTriggered(self, removed_printers_message: Message, action: str) -> None:
        if action == "keep_printer_configurations_action":
            removed_printers_message.hide()
        elif action == "remove_printers_action":
            machine_manager = CuraApplication.getInstance().getMachineManager()
            remove_printers_ids = {self._um_cloud_printers[i].getId() for i in self.reported_device_ids}
            all_ids = {m.getId() for m in CuraApplication.getInstance().getContainerRegistry().findContainerStacks(type = "machine")}

            question_title = self.i18n_catalog.i18nc("@title:window", "Remove printers?")
            question_content = self.i18n_catalog.i18ncp(
                "@label",
                "You are about to remove {0} printer from Cura. This action cannot be undone.\nAre you sure you want to continue?",
                "You are about to remove {0} printers from Cura. This action cannot be undone.\nAre you sure you want to continue?",
                len(remove_printers_ids)
            )
            if remove_printers_ids == all_ids:
                question_content = self.i18n_catalog.i18nc("@label", "You are about to remove all printers from Cura. This action cannot be undone.\nAre you sure you want to continue?")
            result = QMessageBox.question(None, question_title, question_content)
            if result == QMessageBox.No:
                return

            for machine_cloud_id in self.reported_device_ids:
                machine_manager.setActiveMachine(self._um_cloud_printers[machine_cloud_id].getId())
                machine_manager.removeMachine(self._um_cloud_printers[machine_cloud_id].getId())
            removed_printers_message.hide()
