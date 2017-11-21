# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from UM.Logger import Logger
from UM.Application import Application
from UM.Signal import Signal, signalemitter

from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange, ServiceInfo
from queue import Queue
from threading import Event, Thread

from time import time

from . import ClusterUM3OutputDevice, LegacyUM3OutputDevice

##      This plugin handles the connection detection & creation of output device objects for the UM3 printer.
#       Zero-Conf is used to detect printers, which are saved in a dict.
#       If we discover a printer that has the same key as the active machine instance a connection is made.
@signalemitter
class UM3OutputDevicePlugin(OutputDevicePlugin):
    addDeviceSignal = Signal()
    removeDeviceSignal = Signal()
    discoveredDevicesChanged = Signal()

    def __init__(self):
        super().__init__()
        self._zero_conf = None
        self._zero_conf_browser = None

        # Because the model needs to be created in the same thread as the QMLEngine, we use a signal.
        self.addDeviceSignal.connect(self._onAddDevice)
        self.removeDeviceSignal.connect(self._onRemoveDevice)

        Application.getInstance().globalContainerStackChanged.connect(self.reCheckConnections)

        self._discovered_devices = {}

        # The zero-conf service changed requests are handled in a separate thread, so we can re-schedule the requests
        # which fail to get detailed service info.
        # Any new or re-scheduled requests will be appended to the request queue, and the handling thread will pick
        # them up and process them.
        self._service_changed_request_queue = Queue()
        self._service_changed_request_event = Event()
        self._service_changed_request_thread = Thread(target=self._handleOnServiceChangedRequests, daemon=True)
        self._service_changed_request_thread.start()

    def getDiscoveredDevices(self):
        return self._discovered_devices

    ##  Start looking for devices on network.
    def start(self):
        self.startDiscovery()

    def startDiscovery(self):
        self.stop()
        if self._zero_conf_browser:
            self._zero_conf_browser.cancel()
            self._zero_conf_browser = None  # Force the old ServiceBrowser to be destroyed.

        self._zero_conf = Zeroconf()
        self._zero_conf_browser = ServiceBrowser(self._zero_conf, u'_ultimaker._tcp.local.',
                                                 [self._appendServiceChangedRequest])

    def reCheckConnections(self):
        active_machine = Application.getInstance().getGlobalContainerStack()
        if not active_machine:
            return

        um_network_key = active_machine.getMetaDataEntry("um_network_key")

        for key in self._discovered_devices:
            if key == um_network_key:
                if not self._discovered_devices[key].isConnected():
                    Logger.log("d", "Attempting to connect with [%s]" % key)
                    self._discovered_devices[key].connect()
                    self._discovered_devices[key].connectionStateChanged.connect(self._onDeviceConnectionStateChanged)
            else:
                if self._discovered_devices[key].isConnected():
                    Logger.log("d", "Attempting to close connection with [%s]" % key)
                    self._discovered_devices[key].close()
                    self._discovered_devices[key].connectionStateChanged.disconnect(self._onDeviceConnectionStateChanged)

    def _onDeviceConnectionStateChanged(self, key):
        if key not in self._discovered_devices:
            return

        if self._discovered_devices[key].isConnected():
            self.getOutputDeviceManager().addOutputDevice(self._discovered_devices[key])
        else:
            self.getOutputDeviceManager().removeOutputDevice(key)

    def stop(self):
        if self._zero_conf is not None:
            Logger.log("d", "zeroconf close...")
            self._zero_conf.close()

    def _onRemoveDevice(self, name):
        device = self._discovered_devices.pop(name, None)
        if device:
            if device.isConnected():
                device.disconnect()
                device.connectionStateChanged.disconnect(self._onDeviceConnectionStateChanged)

            self.discoveredDevicesChanged.emit()

    def _onAddDevice(self, name, address, properties):
        # Check what kind of device we need to add; Depending on the firmware we either add a "Connect"/"Cluster"
        # or "Legacy" UM3 device.
        cluster_size = int(properties.get(b"cluster_size", -1))
        if cluster_size > 0:
            device = ClusterUM3OutputDevice.ClusterUM3OutputDevice(name, address, properties)
        else:
            device = LegacyUM3OutputDevice.LegacyUM3OutputDevice(name, address, properties)

        self._discovered_devices[device.getId()] = device
        self.discoveredDevicesChanged.emit()

        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack and device.getId() == global_container_stack.getMetaDataEntry("um_network_key"):
            device.connect()
            device.connectionStateChanged.connect(self._onDeviceConnectionStateChanged)

    ##  Appends a service changed request so later the handling thread will pick it up and processes it.
    def _appendServiceChangedRequest(self, zeroconf, service_type, name, state_change):
        # append the request and set the event so the event handling thread can pick it up
        item = (zeroconf, service_type, name, state_change)
        self._service_changed_request_queue.put(item)
        self._service_changed_request_event.set()

    def _handleOnServiceChangedRequests(self):
        while True:
            # Wait for the event to be set
            self._service_changed_request_event.wait(timeout = 5.0)

            # Stop if the application is shutting down
            if Application.getInstance().isShuttingDown():
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
    #   Note that this function can take over 3 seconds to complete. Be carefull calling it from the main thread.
    def _onServiceChanged(self, zero_conf, service_type, name, state_change):
        if state_change == ServiceStateChange.Added:
            Logger.log("d", "Bonjour service added: %s" % name)

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
                Logger.log("d", "Trying to get address of %s", name)
                info = zero_conf.get_service_info(service_type, name)

            if info:
                type_of_device = info.properties.get(b"type", None)
                if type_of_device:
                    if type_of_device == b"printer":
                        address = '.'.join(map(lambda n: str(n), info.address))
                        self.addDeviceSignal.emit(str(name), address, info.properties)
                    else:
                        Logger.log("w",
                                   "The type of the found device is '%s', not 'printer'! Ignoring.." % type_of_device)
            else:
                Logger.log("w", "Could not get information about %s" % name)
                return False

        elif state_change == ServiceStateChange.Removed:
            Logger.log("d", "Bonjour service removed: %s" % name)
            self.removeDeviceSignal.emit(str(name))

        return True