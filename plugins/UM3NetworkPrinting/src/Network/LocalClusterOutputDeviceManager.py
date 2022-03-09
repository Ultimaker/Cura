# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Dict, Optional, Callable, List

from UM import i18nCatalog
from UM.Logger import Logger
from UM.Signal import Signal
from UM.Version import Version

from cura.CuraApplication import CuraApplication
from cura.Settings.CuraStackBuilder import CuraStackBuilder
from cura.Settings.GlobalStack import GlobalStack

from .ZeroConfClient import ZeroConfClient
from .ClusterApiClient import ClusterApiClient
from .LocalClusterOutputDevice import LocalClusterOutputDevice
from ..UltimakerNetworkedPrinterOutputDevice import UltimakerNetworkedPrinterOutputDevice
from ..Messages.CloudFlowMessage import CloudFlowMessage
from ..Messages.LegacyDeviceNoLongerSupportedMessage import LegacyDeviceNoLongerSupportedMessage
from ..Models.Http.PrinterSystemStatus import PrinterSystemStatus


I18N_CATALOG = i18nCatalog("cura")


class LocalClusterOutputDeviceManager:
    """The LocalClusterOutputDeviceManager is responsible for discovering and managing local networked clusters."""


    META_NETWORK_KEY = "um_network_key"

    MANUAL_DEVICES_PREFERENCE_KEY = "um3networkprinting/manual_instances"
    MIN_SUPPORTED_CLUSTER_VERSION = Version("4.0.0")

    # The translation catalog for this device.
    I18N_CATALOG = i18nCatalog("cura")

    # Signal emitted when the list of discovered devices changed.
    discoveredDevicesChanged = Signal()

    def __init__(self) -> None:

        # Persistent dict containing the networked clusters.
        self._discovered_devices = {}  # type: Dict[str, LocalClusterOutputDevice]
        self._output_device_manager = CuraApplication.getInstance().getOutputDeviceManager()

        # Hook up ZeroConf client.
        self._zero_conf_client = ZeroConfClient()
        self._zero_conf_client.addedNetworkCluster.connect(self._onDeviceDiscovered)
        self._zero_conf_client.removedNetworkCluster.connect(self._onDiscoveredDeviceRemoved)

    def start(self) -> None:
        """Start the network discovery."""
        self._zero_conf_client.start()
        for address in self._getStoredManualAddresses():
            self.addManualDevice(address)

    def stop(self) -> None:
        """Stop network discovery and clean up discovered devices."""

        self._zero_conf_client.stop()
        for instance_name in list(self._discovered_devices):
            self._onDiscoveredDeviceRemoved(instance_name)

    def startDiscovery(self):
        """Restart discovery on the local network."""

        self.stop()
        self.start()

    def addManualDevice(self, address: str, callback: Optional[Callable[[bool, str], None]] = None) -> None:
        """Add a networked printer manually by address."""

        api_client = ClusterApiClient(address, lambda error: Logger.log("e", str(error)))
        api_client.getSystem(lambda status: self._onCheckManualDeviceResponse(address, status, callback))

    def removeManualDevice(self, device_id: str, address: Optional[str] = None) -> None:
        """Remove a manually added networked printer."""

        if device_id not in self._discovered_devices and address is not None:
            device_id = "manual:{}".format(address)

        if device_id in self._discovered_devices:
            address = address or self._discovered_devices[device_id].ipAddress
            self._onDiscoveredDeviceRemoved(device_id)

        if address in self._getStoredManualAddresses():
            self._removeStoredManualAddress(address)

    def refreshConnections(self) -> None:
        """Force reset all network device connections."""

        self._connectToActiveMachine()

    def getDiscoveredDevices(self) -> Dict[str, LocalClusterOutputDevice]:
        """Get the discovered devices."""

        return self._discovered_devices

    def associateActiveMachineWithPrinterDevice(self, device: LocalClusterOutputDevice) -> None:
        """Connect the active machine to a given device."""

        active_machine = CuraApplication.getInstance().getGlobalContainerStack()
        if not active_machine:
            return
        self._connectToOutputDevice(device, active_machine)
        self._connectToActiveMachine()

        # Pre-select the correct machine type of the group host.
        # We first need to find the correct definition because the machine manager only takes name as input, not ID.
        definitions = CuraApplication.getInstance().getContainerRegistry().findContainers(id = device.printerType)
        if not definitions:
            return
        CuraApplication.getInstance().getMachineManager().switchPrinterType(definitions[0].getName())

    def _connectToActiveMachine(self) -> None:
        """Callback for when the active machine was changed by the user or a new remote cluster was found."""

        active_machine = CuraApplication.getInstance().getGlobalContainerStack()
        if not active_machine:
            return

        output_device_manager = CuraApplication.getInstance().getOutputDeviceManager()
        stored_device_id = active_machine.getMetaDataEntry(self.META_NETWORK_KEY)
        for device in self._discovered_devices.values():
            if device.key == stored_device_id:
                # Connect to it if the stored key matches.
                self._connectToOutputDevice(device, active_machine)
            elif device.key in output_device_manager.getOutputDeviceIds():
                # Remove device if it is not meant for the active machine.
                output_device_manager.removeOutputDevice(device.key)

    def _onCheckManualDeviceResponse(self, address: str, status: PrinterSystemStatus,
                                     callback: Optional[Callable[[bool, str], None]] = None) -> None:
        """Callback for when a manual device check request was responded to."""

        self._onDeviceDiscovered("manual:{}".format(address), address, {
            b"name": status.name.encode("utf-8"),
            b"address": address.encode("utf-8"),
            b"machine": str(status.hardware.get("typeid", "")).encode("utf-8"),
            b"manual": b"true",
            b"firmware_version": status.firmware.encode("utf-8"),
            b"cluster_size": b"1"
        })
        self._storeManualAddress(address)
        if callback is not None:
            CuraApplication.getInstance().callLater(callback, True, address)

    @staticmethod
    def _getPrinterTypeIdentifiers() -> Dict[str, str]:
        """Returns a dict of printer BOM numbers to machine types.

        These numbers are available in the machine definition already so we just search for them here.
        """

        container_registry = CuraApplication.getInstance().getContainerRegistry()
        ultimaker_machines = container_registry.findContainersMetadata(type="machine", manufacturer="Ultimaker B.V.")
        found_machine_type_identifiers = {}  # type: Dict[str, str]
        for machine in ultimaker_machines:
            machine_type = machine.get("id", None)
            machine_bom_numbers = machine.get("bom_numbers", [])
            if machine_type and machine_bom_numbers:
                for bom_number in machine_bom_numbers:
                    # This produces a n:1 mapping of bom numbers to machine types
                    # allowing the S5R1 and S5R2 hardware to use a single S5 definition.
                    found_machine_type_identifiers[str(bom_number)] = machine_type
        return found_machine_type_identifiers

    def _onDeviceDiscovered(self, key: str, address: str, properties: Dict[bytes, bytes]) -> None:
        """Add a new device."""

        machine_identifier = properties.get(b"machine", b"").decode("utf-8")
        printer_type_identifiers = self._getPrinterTypeIdentifiers()

        # Detect the machine type based on the BOM number that is sent over the network.
        properties[b"printer_type"] = b"Unknown"
        for bom, p_type in printer_type_identifiers.items():
            if machine_identifier.startswith(bom):
                properties[b"printer_type"] = bytes(p_type, encoding="utf8")
                break

        device = LocalClusterOutputDevice(key, address, properties)
        discovered_printers_model = CuraApplication.getInstance().getDiscoveredPrintersModel()
        if address in list(discovered_printers_model.discoveredPrintersByAddress.keys()):
            # The printer was already added, we just update the available data.
            discovered_printers_model.updateDiscoveredPrinter(
                ip_address=address,
                name=device.getName(),
                machine_type=device.printerType
            )
        else:
            # The printer was not added yet so let's do that.
            discovered_printers_model.addDiscoveredPrinter(
                ip_address=address,
                key=device.getId(),
                name=device.getName(),
                create_callback=self._createMachineFromDiscoveredDevice,
                machine_type=device.printerType,
                device=device
            )
        self._discovered_devices[device.getId()] = device
        self.discoveredDevicesChanged.emit()
        self._connectToActiveMachine()

    def _onDiscoveredDeviceRemoved(self, device_id: str) -> None:
        """Remove a device."""

        device = self._discovered_devices.pop(device_id, None)  # type: Optional[LocalClusterOutputDevice]
        if not device:
            return
        device.close()
        CuraApplication.getInstance().getDiscoveredPrintersModel().removeDiscoveredPrinter(device.address)
        self.discoveredDevicesChanged.emit()

    def _createMachineFromDiscoveredDevice(self, device_id: str) -> None:
        """Create a machine instance based on the discovered network printer."""

        device = self._discovered_devices.get(device_id)
        if device is None:
            return

        # Create a new machine and activate it.
        # We do not use use MachineManager.addMachine here because we need to set the network key before activating it.
        # If we do not do this the auto-pairing with the cloud-equivalent device will not work.
        new_machine = CuraStackBuilder.createMachine(device.name, device.printerType)
        if not new_machine:
            Logger.log("e", "Failed creating a new machine")
            return
        new_machine.setMetaDataEntry(self.META_NETWORK_KEY, device.key)
        CuraApplication.getInstance().getMachineManager().setActiveMachine(new_machine.getId())
        self._connectToOutputDevice(device, new_machine)
        self._showCloudFlowMessage(device)

    def _storeManualAddress(self, address: str) -> None:
        """Add an address to the stored preferences."""

        stored_addresses = self._getStoredManualAddresses()
        if address in stored_addresses:
            return  # Prevent duplicates.
        stored_addresses.append(address)
        new_value = ",".join(stored_addresses)
        CuraApplication.getInstance().getPreferences().setValue(self.MANUAL_DEVICES_PREFERENCE_KEY, new_value)

    def _removeStoredManualAddress(self, address: str) -> None:
        """Remove an address from the stored preferences."""

        stored_addresses = self._getStoredManualAddresses()
        try:
            stored_addresses.remove(address)  # Can throw a ValueError
            new_value = ",".join(stored_addresses)
            CuraApplication.getInstance().getPreferences().setValue(self.MANUAL_DEVICES_PREFERENCE_KEY, new_value)
        except ValueError:
            Logger.log("w", "Could not remove address from stored_addresses, it was not there")

    def _getStoredManualAddresses(self) -> List[str]:
        """Load the user-configured manual devices from Cura preferences."""

        preferences = CuraApplication.getInstance().getPreferences()
        preferences.addPreference(self.MANUAL_DEVICES_PREFERENCE_KEY, "")
        manual_instances = preferences.getValue(self.MANUAL_DEVICES_PREFERENCE_KEY).split(",")
        return manual_instances

    def _connectToOutputDevice(self, device: UltimakerNetworkedPrinterOutputDevice, machine: GlobalStack) -> None:
        """Add a device to the current active machine."""

        # Make sure users know that we no longer support legacy devices.
        if Version(device.firmwareVersion) < self.MIN_SUPPORTED_CLUSTER_VERSION:
            LegacyDeviceNoLongerSupportedMessage().show()
            return

        machine.setName(device.name)
        machine.setMetaDataEntry(self.META_NETWORK_KEY, device.key)
        machine.setMetaDataEntry("group_name", device.name)
        machine.addConfiguredConnectionType(device.connectionType.value)

        if not device.isConnected():
            device.connect()

        output_device_manager = CuraApplication.getInstance().getOutputDeviceManager()
        if device.key not in output_device_manager.getOutputDeviceIds():
            output_device_manager.addOutputDevice(device)

    @staticmethod
    def _showCloudFlowMessage(device: LocalClusterOutputDevice) -> None:
        """Nudge the user to start using Ultimaker Cloud."""

        if CuraApplication.getInstance().getMachineManager().activeMachineHasCloudRegistration:
            # This printer is already cloud connected, so we do not bother the user anymore.
            return
        if not CuraApplication.getInstance().getCuraAPI().account.isLoggedIn:
            # Do not show the message if the user is not signed in.
            return
        CloudFlowMessage(device.name).show()
