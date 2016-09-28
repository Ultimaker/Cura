from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from . import NetworkPrinterOutputDevice

from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange, ServiceInfo
from UM.Logger import Logger
from UM.Signal import Signal, signalemitter
from UM.Application import Application
from UM.Preferences import Preferences

from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager, QNetworkReply
from PyQt5.QtCore import QUrl

import time

##      This plugin handles the connection detection & creation of output device objects for the UM3 printer.
#       Zero-Conf is used to detect printers, which are saved in a dict.
#       If we discover a printer that has the same key as the active machine instance a connection is made.
@signalemitter
class NetworkPrinterOutputDevicePlugin(OutputDevicePlugin):
    def __init__(self):
        super().__init__()
        self._zero_conf = Zeroconf()
        self._browser = None
        self._printers = {}

        self._api_version = "1"
        self._api_prefix = "/api/v" + self._api_version + "/"

        self._network_manager = QNetworkAccessManager()
        self._network_manager.finished.connect(self._onNetworkRequestFinished)

        # List of old printer names. This is used to ensure that a refresh of zeroconf does not needlessly forces
        # authentication requests.
        self._old_printers = []

        # Because the model needs to be created in the same thread as the QMLEngine, we use a signal.
        self.addPrinterSignal.connect(self.addPrinter)
        self.removePrinterSignal.connect(self.removePrinter)
        Application.getInstance().globalContainerStackChanged.connect(self.reCheckConnections)

        # Get list of manual printers from preferences
        preferences = Preferences.getInstance()
        preferences.addPreference("um3networkprinting/manual_instances", "") #  A comma-separated list of ip adresses or hostnames
        self._manual_instances = preferences.getValue("um3networkprinting/manual_instances").split(",")

    addPrinterSignal = Signal()
    removePrinterSignal = Signal()
    printerListChanged = Signal()

    ##  Start looking for devices on network.
    def start(self):
        self.startDiscovery()

    def startDiscovery(self):
        if self._browser:
            self._browser.cancel()
            self._browser = None
            self._old_printers = [printer_name for printer_name in self._printers]
            self._printers = {}

        self._browser = ServiceBrowser(self._zero_conf, u'_ultimaker._tcp.local.', [self._onServiceChanged])

        # Look for manual instances from preference
        for address in self._manual_instances:
            url = QUrl("http://" + address + self._api_prefix + "system/name")

            name_request = QNetworkRequest(url)
            self._network_manager.get(name_request)

    ##  Handler for all requests that have finished.
    def _onNetworkRequestFinished(self, reply):
        reply_url = reply.url().toString()
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)

        if reply.operation() == QNetworkAccessManager.GetOperation:
            if "system/name" in reply_url:  # Name returned from printer.
                if status_code == 200:
                    address = reply.url().host()
                    name = reply.readAll()

                    instance_name = "manual:%s" % address
                    properties = { b"name": name.data() }
                    self.addPrinter(instance_name, address, properties)

    ##  Stop looking for devices on network.
    def stop(self):
        self._zero_conf.close()

    def getPrinters(self):
        return self._printers

    def reCheckConnections(self):
        active_machine = Application.getInstance().getGlobalContainerStack()
        if not active_machine:
            return

        for key in self._printers:
            if key == active_machine.getMetaDataEntry("um_network_key"):
                self._printers[key].connect()
                self._printers[key].connectionStateChanged.connect(self._onPrinterConnectionStateChanged)
            else:
                if self._printers[key].isConnected():
                    self._printers[key].close()

    ##  Because the model needs to be created in the same thread as the QMLEngine, we use a signal.
    def addPrinter(self, name, address, properties):
        printer = NetworkPrinterOutputDevice.NetworkPrinterOutputDevice(name, address, properties)
        self._printers[printer.getKey()] = printer
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack and printer.getKey() == global_container_stack.getMetaDataEntry("um_network_key"):
            if printer.getKey() not in self._old_printers:  # Was the printer already connected, but a re-scan forced?
                self._printers[printer.getKey()].connect()
                printer.connectionStateChanged.connect(self._onPrinterConnectionStateChanged)
        self.printerListChanged.emit()

    def removePrinter(self, name):
        printer = self._printers.pop(name, None)
        if printer:
            if printer.isConnected():
                printer.connectionStateChanged.disconnect(self._onPrinterConnectionStateChanged)
                printer.disconnect()
        self.printerListChanged.emit()

    ##  Handler for when the connection state of one of the detected printers changes
    def _onPrinterConnectionStateChanged(self, key):
        if key not in self._printers:
            return
        if self._printers[key].isConnected():
            self.getOutputDeviceManager().addOutputDevice(self._printers[key])
        else:
            self.getOutputDeviceManager().removeOutputDevice(key)

    ##  Handler for zeroConf detection
    def _onServiceChanged(self, zeroconf, service_type, name, state_change):
        if state_change == ServiceStateChange.Added:
            Logger.log("d", "Bonjour service added: %s" % name)

            # First try getting info from zeroconf cache
            info = ServiceInfo(service_type, name, properties = {})
            for record in zeroconf.cache.entries_with_name(name.lower()):
                info.update_record(zeroconf, time.time(), record)

            for record in zeroconf.cache.entries_with_name(info.server):
                info.update_record(zeroconf, time.time(), record)
                if info.address:
                    break

            # Request more data if info is not complete
            if not info.address:
                Logger.log("d", "Trying to get address of %s", name)
                info = zeroconf.get_service_info(service_type, name)

            if info:
                if info.properties.get(b"type", None) == b'printer':
                    address = '.'.join(map(lambda n: str(n), info.address))
                    self.addPrinterSignal.emit(str(name), address, info.properties)
            else:
                Logger.log("w", "Could not get information about %s" % name)

        elif state_change == ServiceStateChange.Removed:
            Logger.log("d", "Bonjour service removed: %s" % name)
            self.removePrinterSignal.emit(str(name))