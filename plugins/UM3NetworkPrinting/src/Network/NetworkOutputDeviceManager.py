# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from queue import Queue
from threading import Thread, Event
from time import time
from typing import Dict, Optional, Callable

from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange, ServiceInfo

from UM import i18nCatalog
from UM.Logger import Logger
from UM.Message import Message
from UM.Signal import Signal
from UM.Version import Version

from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.PrinterOutputDevice import PrinterOutputDevice
from cura.Settings.GlobalStack import GlobalStack

from .ClusterApiClient import ClusterApiClient
from .NetworkOutputDevice import NetworkOutputDevice
from .ManualPrinterRequest import ManualPrinterRequest


## The NetworkOutputDeviceManager is responsible for discovering and managing local networked clusters.
class NetworkOutputDeviceManager:

    ZERO_CONF_NAME = u"_ultimaker._tcp.local."
    MANUAL_DEVICES_PREFERENCE_KEY = "um3networkprinting/manual_instances"
    MIN_SUPPORTED_CLUSTER_VERSION = Version("4.0.0")

    # The translation catalog for this device.
    I18N_CATALOG = i18nCatalog("cura")

    discoveredDevicesChanged = Signal()
    addedNetworkCluster = Signal()
    removedNetworkCluster = Signal()

    def __init__(self) -> None:

        # Persistent dict containing the networked clusters.
        self._discovered_devices = {}  # type: Dict[str, NetworkOutputDevice]
        self._output_device_manager = CuraApplication.getInstance().getOutputDeviceManager()

        # TODO: move zeroconf stuff to own class?
        self._zero_conf = None  # type: Optional[Zeroconf]
        self._zero_conf_browser = None  # type: Optional[ServiceBrowser]
        self._service_changed_request_queue = None  # type: Optional[Queue]
        self._service_changed_request_event = None  # type: Optional[Event]
        self._service_changed_request_thread = None  # type: Optional[Thread]

        # TODO: move manual device stuff to own class?
        # Persistent dict containing manually connected clusters.
        self._manual_instances = {}  # type: Dict[str, ManualPrinterRequest]
        self._last_manual_entry_key = None  # type: Optional[str]

        # Hook up the signals for discovery.
        self.addedNetworkCluster.connect(self._onAddDevice)
        self.removedNetworkCluster.connect(self._onRemoveDevice)

    ## Start the network discovery.
    def start(self):
        # The ZeroConf service changed requests are handled in a separate thread so we don't block the UI.
        # We can also re-schedule the requests when they fail to get detailed service info.
        # Any new or re-reschedule requests will be appended to the request queue and the thread will process them.
        self._service_changed_request_queue = Queue()
        self._service_changed_request_event = Event()
        self._service_changed_request_thread = Thread(target=self._handleOnServiceChangedRequests, daemon=True)
        self._service_changed_request_thread.start()

        # Start network discovery.
        self.stop()
        self._zero_conf = Zeroconf()
        self._zero_conf_browser = ServiceBrowser(self._zero_conf, self.ZERO_CONF_NAME, [
            self._appendServiceChangedRequest
        ])

        # Load all manual devices.
        self._manual_instances = self._getStoredManualInstances()
        for address in self._manual_instances:
            if address:
                self.addManualDevice(address)

    ## Stop network discovery and clean up discovered devices.
    def stop(self):
        # Cleanup ZeroConf resources.
        if self._zero_conf is not None:
            self._zero_conf.close()
            self._zero_conf = None
        if self._zero_conf_browser is not None:
            self._zero_conf_browser.cancel()
            self._zero_conf_browser = None

        # Cleanup all manual devices.
        for instance_name in list(self._discovered_devices):
            self._onRemoveDevice(instance_name)

    ## Add a networked printer manually by address.
    def addManualDevice(self, address: str, callback: Optional[Callable[[bool, str], None]] = None) -> None:
        self._manual_instances[address] = ManualPrinterRequest(address, callback=callback)
        new_manual_devices = ",".join(self._manual_instances.keys())
        CuraApplication.getInstance().getPreferences().setValue(self.MANUAL_DEVICES_PREFERENCE_KEY, new_manual_devices)

        key = f"manual:{address}"
        if key not in self._discovered_devices:
            self._onAddDevice(key, address, {
                b"name": address.encode("utf-8"),
                b"address": address.encode("utf-8"),
                b"manual": b"true",
                b"incomplete": b"true",
                b"temporary": b"true"
            })

        self._last_manual_entry_key = key
        response_callback = lambda status_code, response: self._onCheckManualDeviceResponse(status_code, address)
        self._checkManualDevice(address, response_callback)

    ## Remove a manually added networked printer.
    def removeManualDevice(self, key: str, address: Optional[str] = None) -> None:
        if key not in self._discovered_devices and address is not None:
            key = f"manual:{address}"

        if key in self._discovered_devices:
            if not address:
                address = self._discovered_devices[key].ipAddress
            self._onRemoveDevice(key)

        if address in self._manual_instances:
            manual_printer_request = self._manual_instances.pop(address)
            new_manual_devices = ",".join(self._manual_instances.keys())
            CuraApplication.getInstance().getPreferences().setValue(self.MANUAL_DEVICES_PREFERENCE_KEY,
                                                                    new_manual_devices)
            if manual_printer_request.callback is not None:
                CuraApplication.getInstance().callLater(manual_printer_request.callback, False, address)

    ## Force reset all network device connections.
    def refreshConnections(self):
        self._connectToActiveMachine()

    ##  Callback for when the active machine was changed by the user or a new remote cluster was found.
    def _connectToActiveMachine(self):
        active_machine = CuraApplication.getInstance().getGlobalContainerStack()
        if not active_machine:
            return

        for device_id in self._discovered_devices:
            CuraApplication.getInstance().getOutputDeviceManager().removeOutputDevice(device_id)

        stored_network_key = active_machine.getMetaDataEntry("um_network_key")
        if stored_network_key in self._discovered_devices:
            device = self._discovered_devices[stored_network_key]
            self._connectToOutputDevice(device, active_machine)

    ## Add a device to the current active machine.
    @staticmethod
    def _connectToOutputDevice(device: PrinterOutputDevice, active_machine: GlobalStack) -> None:
        device.connect()
        active_machine.setMetaDataEntry("um_network_key", device.key)
        active_machine.setMetaDataEntry("group_name", device.name)
        active_machine.addConfiguredConnectionType(device.connectionType.value)
        CuraApplication.getInstance().getOutputDeviceManager().addOutputDevice(device)

    ## Handles an API error received from the cloud.
    #  \param errors: The errors received
    def _onApiError(self, errors) -> None:
        Logger.log("w", str(errors))
        message = Message(
            text=self.I18N_CATALOG.i18nc("@info:description", "There was an error connecting to the printer."),
            title=self.I18N_CATALOG.i18nc("@info:title", "Error"),
            lifetime=10
        )
        message.show()

    ## Checks if a networked printer exists at the given address.
    #  If the printer responds it will replace the preliminary printer created from the stored manual instances.
    def _checkManualDevice(self, address: str, on_finished: Callable) -> None:
        api_client = ClusterApiClient(address, self._onApiError)
        api_client.getSystem(on_finished)

    ## Callback for when a manual device check request was responded to.
    def _onCheckManualDeviceResponse(self, status_code: int, address: str) -> None:
        Logger.log("d", "manual device check response: {} {}".format(status_code, address))
        if address in self._manual_instances:
            callback = self._manual_instances[address].callback
            if callback:
                CuraApplication.getInstance().callLater(callback, status_code == 200, address)

    ##  Returns a dict of printer BOM numbers to machine types.
    #   These numbers are available in the machine definition already so we just search for them here.
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
    def _onAddDevice(self, key: str, address: str, properties: Dict[bytes, bytes]) -> None:
        cluster_size = int(properties.get(b"cluster_size", -1))
        printer_type = properties.get(b"machine", b"").decode("utf-8")
        printer_type_identifiers = self._getPrinterTypeIdentifiers()

        # Detect the machine type based on the BOM number that is sent over the network.
        for bom, p_type in printer_type_identifiers.items():
            if printer_type.startswith(bom):
                properties[b"printer_type"] = bytes(p_type, encoding="utf8")
                break
        else:
            properties[b"printer_type"] = b"Unknown"

        # We no longer support legacy devices, so check that here.
        if cluster_size == -1:
            return

        device = NetworkOutputDevice(key, address, properties)

        CuraApplication.getInstance().getDiscoveredPrintersModel().addDiscoveredPrinter(
            ip_address=address,
            key=device.getId(),
            name=properties[b"name"].decode("utf-8"),
            create_callback=self._createMachineFromDiscoveredPrinter,
            machine_type=properties[b"printer_type"].decode("utf-8"),
            device=device
        )

        self._discovered_devices[device.getId()] = device
        self.discoveredDevicesChanged.emit()
        self._connectToActiveMachine()

    ## Remove a device.
    def _onRemoveDevice(self, device_id: str) -> None:
        device = self._discovered_devices.pop(device_id, None)
        if not device:
            return
        if device.isConnected():
            device.disconnect()
        CuraApplication.getInstance().getDiscoveredPrintersModel().removeDiscoveredPrinter(device.address)
        self.discoveredDevicesChanged.emit()

    ## Appends a service changed request so later the handling thread will pick it up and processes it.
    def _appendServiceChangedRequest(self, zeroconf: Zeroconf, service_type, name: str,
                                     state_change: ServiceStateChange) -> None:
        item = (zeroconf, service_type, name, state_change)
        self._service_changed_request_queue.put(item)
        self._service_changed_request_event.set()

    def _handleOnServiceChangedRequests(self) -> None:
        while True:
            # Wait for the event to be set
            self._service_changed_request_event.wait(timeout=5.0)

            # Stop if the application is shutting down
            if CuraApplication.getInstance().isShuttingDown():
                return

            self._service_changed_request_event.clear()

            # Handle all pending requests
            reschedule_requests = []  # A list of requests that have failed so later they will get re-scheduled
            while not self._service_changed_request_queue.empty():
                request = self._service_changed_request_queue.get()
                zeroconf, service_type, name, state_change = request
                try:
                    result = self._onServiceChanged(zeroconf, service_type, name, state_change)
                    if not result:
                        reschedule_requests.append(request)
                except Exception:
                    Logger.logException("e", "Failed to get service info for [%s] [%s], the request will be rescheduled",
                                        service_type, name)
                    reschedule_requests.append(request)

            # Re-schedule the failed requests if any
            if reschedule_requests:
                for request in reschedule_requests:
                    self._service_changed_request_queue.put(request)

    ##  Handler for zeroConf detection.
    #   Return True or False indicating if the process succeeded.
    #   Note that this function can take over 3 seconds to complete. Be careful calling it from the main thread.
    def _onServiceChanged(self, zero_conf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange
                          ) -> bool:
        if state_change == ServiceStateChange.Added:
            return self._onServiceAdded(zero_conf, service_type, name)
        elif state_change == ServiceStateChange.Removed:
            return self._onServiceRemoved(name)
        return True

    ## Handler for when a ZeroConf service was added.
    def _onServiceAdded(self, zero_conf: Zeroconf, service_type: str, name: str) -> bool:
        # First try getting info from zero-conf cache
        info = ServiceInfo(service_type, name, properties={})
        for record in zero_conf.cache.entries_with_name(name.lower()):
            info.update_record(zero_conf, time(), record)

        for record in zero_conf.cache.entries_with_name(info.server):
            info.update_record(zero_conf, time(), record)
            if info.address:
                break

        # Request more data if info is not complete
        if not info.address:
            info = zero_conf.get_service_info(service_type, name)

        if info:
            type_of_device = info.properties.get(b"type", None)
            if type_of_device:
                if type_of_device == b"printer":
                    address = '.'.join(map(lambda n: str(n), info.address))
                    self.addedNetworkCluster.emit(str(name), address, info.properties)
                else:
                    Logger.log("w",
                               "The type of the found device is '%s', not 'printer'! Ignoring.." % type_of_device)
        else:
            Logger.log("w", "Could not get information about %s" % name)
            return False

        return True

    ## Handler for when a ZeroConf service was removed.
    def _onServiceRemoved(self, name: str) -> bool:
        Logger.log("d", "Bonjour service removed: %s" % name)
        self.removedNetworkCluster.emit(str(name))
        return True

    ## Create a machine instance based on the discovered network printer.
    def _createMachineFromDiscoveredPrinter(self, key: str) -> None:
        discovered_device = self._discovered_devices.get(key)
        if discovered_device is None:
            Logger.log("e", "Could not find discovered device with key [%s]", key)
            return
        group_name = discovered_device.getProperty("name")
        machine_type_id = discovered_device.getProperty("printer_type")
        Logger.log("i", "Creating machine from network device with key = [%s], group name = [%s],  printer type = [%s]",
                   key, group_name, machine_type_id)
        CuraApplication.getInstance().getMachineManager().addMachine(machine_type_id, group_name)
        self._connectToActiveMachine()

    ## Load the user-configured manual devices from Cura preferences.
    def _getStoredManualInstances(self) -> Dict[str, ManualPrinterRequest]:
        preferences = CuraApplication.getInstance().getPreferences()
        preferences.addPreference(self.MANUAL_DEVICES_PREFERENCE_KEY, "")
        manual_instances = preferences.getValue(self.MANUAL_DEVICES_PREFERENCE_KEY).split(",")
        return {address: ManualPrinterRequest(address) for address in manual_instances}
