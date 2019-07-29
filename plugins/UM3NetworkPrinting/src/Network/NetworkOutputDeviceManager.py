# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Dict, Optional, Callable

from UM import i18nCatalog
from UM.Logger import Logger
from UM.Signal import Signal
from UM.Version import Version

from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.PrinterOutputDevice import PrinterOutputDevice
from cura.Settings.GlobalStack import GlobalStack

from .ZeroConfClient import ZeroConfClient
from .ClusterApiClient import ClusterApiClient
from .NetworkOutputDevice import NetworkOutputDevice


## The NetworkOutputDeviceManager is responsible for discovering and managing local networked clusters.
class NetworkOutputDeviceManager:

    MANUAL_DEVICES_PREFERENCE_KEY = "um3networkprinting/manual_instances"
    MIN_SUPPORTED_CLUSTER_VERSION = Version("4.0.0")

    # The translation catalog for this device.
    I18N_CATALOG = i18nCatalog("cura")

    # Signal emitted when the list of discovered devices changed.
    discoveredDevicesChanged = Signal()

    def __init__(self) -> None:

        # Persistent dict containing the networked clusters.
        self._discovered_devices = {}  # type: Dict[str, NetworkOutputDevice]
        self._output_device_manager = CuraApplication.getInstance().getOutputDeviceManager()

        # Hook up ZeroConf client.
        self._zero_conf_client = ZeroConfClient()
        self._zero_conf_client.addedNetworkCluster.connect(self._onDeviceDiscovered)
        self._zero_conf_client.removedNetworkCluster.connect(self._onDiscoveredDeviceRemoved)

        # Persistent dict containing manually connected clusters.
        self._manual_instances = {}  # type: Dict[str, Callable]

    ## Start the network discovery.
    def start(self) -> None:
        self._zero_conf_client.start()
        # Load all manual devices.
        self._manual_instances = self._getStoredManualInstances()
        for address in self._manual_instances:
            self.addManualDevice(address)

    ## Stop network discovery and clean up discovered devices.
    def stop(self) -> None:
        self._zero_conf_client.stop()
        # Cleanup all manual devices.
        for instance_name in list(self._discovered_devices):
            self._onDiscoveredDeviceRemoved(instance_name)

    ## Add a networked printer manually by address.
    def addManualDevice(self, address: str, callback: Optional[Callable[[bool, str], None]] = None) -> None:
        self._manual_instances[address] = callback
        new_manual_devices = ",".join(self._manual_instances.keys())
        CuraApplication.getInstance().getPreferences().setValue(self.MANUAL_DEVICES_PREFERENCE_KEY, new_manual_devices)

        device_id = f"manual:{address}"
        if device_id not in self._discovered_devices:
            self._onDeviceDiscovered(device_id, address, {
                b"name": address.encode("utf-8"),
                b"address": address.encode("utf-8"),
                b"manual": b"true",
                b"incomplete": b"true",
                b"temporary": b"true"
            })

        response_callback = lambda status_code, response: self._onCheckManualDeviceResponse(status_code, address)
        self._checkManualDevice(address, response_callback)

    ## Remove a manually added networked printer.
    def removeManualDevice(self, device_id: str, address: Optional[str] = None) -> None:
        if device_id not in self._discovered_devices and address is not None:
            device_id = f"manual:{address}"

        if device_id in self._discovered_devices:
            address = address or self._discovered_devices[device_id].ipAddress
            self._onDiscoveredDeviceRemoved(device_id)

        if address in self._manual_instances:
            manual_instance_callback = self._manual_instances.pop(address)
            new_devices = ",".join(self._manual_instances.keys())
            CuraApplication.getInstance().getPreferences().setValue(self.MANUAL_DEVICES_PREFERENCE_KEY, new_devices)
            if manual_instance_callback:
                CuraApplication.getInstance().callLater(manual_instance_callback, False, address)

    ## Force reset all network device connections.
    def refreshConnections(self):
        self._connectToActiveMachine()

    ##  Callback for when the active machine was changed by the user or a new remote cluster was found.
    def _connectToActiveMachine(self):
        active_machine = CuraApplication.getInstance().getGlobalContainerStack()
        if not active_machine:
            return

        # Remove all output devices that we have registered.
        # This is needed because when we switch we can only leave output devices that are meant for that machine.
        for device_id in self._discovered_devices:
            CuraApplication.getInstance().getOutputDeviceManager().removeOutputDevice(device_id)

        # Check if the stored network key for the active machine is in our list of discovered devices.
        stored_network_key = active_machine.getMetaDataEntry("um_network_key")
        if stored_network_key in self._discovered_devices:
            device = self._discovered_devices[stored_network_key]
            self._connectToOutputDevice(device, active_machine)
            Logger.log("d", "Device connected by metadata network key %s", stored_network_key)

    ## Add a device to the current active machine.
    @staticmethod
    def _connectToOutputDevice(device: PrinterOutputDevice, active_machine: GlobalStack) -> None:
        device.connect()
        active_machine.setMetaDataEntry("um_network_key", device.key)
        active_machine.setMetaDataEntry("group_name", device.name)
        active_machine.addConfiguredConnectionType(device.connectionType.value)
        CuraApplication.getInstance().getOutputDeviceManager().addOutputDevice(device)

    ## Checks if a networked printer exists at the given address.
    #  If the printer responds it will replace the preliminary printer created from the stored manual instances.
    def _checkManualDevice(self, address: str, on_finished: Callable) -> None:
        api_client = ClusterApiClient(address, self._onApiError)
        api_client.getSystem(on_finished)

    ## Callback for when a manual device check request was responded to.
    def _onCheckManualDeviceResponse(self, status_code: int, address: str) -> None:
        Logger.log("d", "manual device check response: {} {}".format(status_code, address))
        if address in self._manual_instances:
            callback = self._manual_instances[address]
            if callback is not None:
                CuraApplication.getInstance().callLater(callback, status_code == 200, address)

    ## Returns a dict of printer BOM numbers to machine types.
    #  These numbers are available in the machine definition already so we just search for them here.
    @staticmethod
    def _getPrinterTypeIdentifiers() -> Dict[str, str]:
        container_registry = CuraApplication.getInstance().getContainerRegistry()
        ultimaker_machines = container_registry.findContainersMetadata(type="machine", manufacturer="Ultimaker B.V.")
        found_machine_type_identifiers = {}  # type: Dict[str, str]
        for machine in ultimaker_machines:
            machine_bom_number = machine.get("firmware_update_info", {}).get("id", None)
            machine_type = machine.get("id", None)
            if machine_bom_number and machine_type:
                found_machine_type_identifiers[str(machine_bom_number)] = machine_type
        return found_machine_type_identifiers

    ## Add a new device.
    def _onDeviceDiscovered(self, key: str, address: str, properties: Dict[bytes, bytes]) -> None:
        cluster_size = int(properties.get(b"cluster_size", -1))
        machine_identifier = properties.get(b"machine", b"").decode("utf-8")
        printer_type_identifiers = self._getPrinterTypeIdentifiers()

        # Detect the machine type based on the BOM number that is sent over the network.
        properties[b"printer_type"] = b"Unknown"
        for bom, p_type in printer_type_identifiers.items():
            if machine_identifier.startswith(bom):
                properties[b"printer_type"] = bytes(p_type, encoding="utf8")
                break

        # We no longer support legacy devices, so check that here.
        if cluster_size == -1:
            return

        device = NetworkOutputDevice(key, address, properties)
        CuraApplication.getInstance().getDiscoveredPrintersModel().addDiscoveredPrinter(
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

    ## Remove a device.
    def _onDiscoveredDeviceRemoved(self, device_id: str) -> None:
        device = self._discovered_devices.pop(device_id, None)
        if not device:
            return
        CuraApplication.getInstance().getDiscoveredPrintersModel().removeDiscoveredPrinter(device.address)
        self.discoveredDevicesChanged.emit()

    ## Create a machine instance based on the discovered network printer.
    def _createMachineFromDiscoveredDevice(self, device_id: str) -> None:
        device = self._discovered_devices.get(device_id)
        if device is None:
            Logger.log("e", "Could not find discovered device with device_id [%s]", device_id)
            return

        # The newly added machine is automatically activated.
        CuraApplication.getInstance().getMachineManager().addMachine(device.printerType, device.name)
        active_machine = CuraApplication.getInstance().getGlobalContainerStack()
        if active_machine:
            self._connectToOutputDevice(device, active_machine)

    ## Load the user-configured manual devices from Cura preferences.
    def _getStoredManualInstances(self) -> Dict[str, Optional[Callable]]:
        preferences = CuraApplication.getInstance().getPreferences()
        preferences.addPreference(self.MANUAL_DEVICES_PREFERENCE_KEY, "")
        manual_instances = preferences.getValue(self.MANUAL_DEVICES_PREFERENCE_KEY).split(",")
        return {address: None for address in manual_instances}

    ## Handles an API error received from the cloud.
    #  \param errors: The errors received
    @staticmethod
    def _onApiError(errors) -> None:
        Logger.log("w", str(errors))
