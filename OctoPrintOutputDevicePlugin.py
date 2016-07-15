from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from . import OctoPrintOutputDevice

from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange, ServiceInfo
from UM.Signal import Signal, signalemitter
from UM.Application import Application

import time

##      This plugin handles the connection detection & creation of output device objects for OctoPrint-connected printers.
#       Zero-Conf is used to detect printers, which are saved in a dict.
#       If we discover a printer that has the same key as the active machine instance a connection is made.
@signalemitter
class OctoPrintOutputDevicePlugin(OutputDevicePlugin):
    def __init__(self):
        super().__init__()
        self._zero_conf = Zeroconf()
        self._browser = None
        self._printers = {}

        # Because the model needs to be created in the same thread as the QMLEngine, we use a signal.
        self.addPrinterSignal.connect(self.addPrinter)
        self.removePrinterSignal.connect(self.removePrinter)
        Application.getInstance().globalContainerStackChanged.connect(self.reCheckConnections)

    addPrinterSignal = Signal()
    removePrinterSignal = Signal()

    ##  Start looking for devices on network.
    def start(self):
        self.startDiscovery()

    def startDiscovery(self):
        if self._browser:
            self._browser.cancel()
            self._browser = None

        self._browser = ServiceBrowser(self._zero_conf, u'_octoprint._tcp.local.', [self._onServiceChanged])

    ##  Stop looking for devices on network.
    def stop(self):
        self._browser.cancel()
        self._browser = None
        self._zero_conf.close()

    def getPrinters(self):
        return self._printers

    def reCheckConnections(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if not global_container_stack:
            return

        for key in self._printers:
            if key == global_container_stack.getMetaDataEntry("octoprint_id"):
                self._printers[key].setApiKey(global_container_stack.getMetaDataEntry("octoprint_api_key", ""))
                self._printers[key].connectionStateChanged.connect(self._onPrinterConnectionStateChanged)
                self._printers[key].connect()
            else:
                if self._printers[key].isConnected():
                    self._printers[key].close()

    ##  Because the model needs to be created in the same thread as the QMLEngine, we use a signal.
    def addPrinter(self, name, address, properties):
        printer = OctoPrintOutputDevice.OctoPrintOutputDevice(name, address, properties)
        self._printers[printer.getKey()] = printer
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack and printer.getKey() == global_container_stack.getMetaDataEntry("octoprint_id"):
            printer.setApiKey(global_container_stack.getMetaDataEntry("octoprint_api_key", ""))
            printer.connectionStateChanged.connect(self._onPrinterConnectionStateChanged)
            printer.connect()

    def removePrinter(self, name):
        printer = self._printers.pop(name, None)
        if printer:
            if printer.isConnected:
                printer.connectionStateChanged.disconnect(self._onPrinterConnectionStateChanged)
                printer.disconnect()

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
            info = ServiceInfo(service_type, name, properties = {})
            for record in zeroconf.cache.entries_with_name(name.lower()):
                info.update_record(zeroconf, time.time(), record)

            for record in zeroconf.cache.entries_with_name(info.server):
                info.update_record(zeroconf, time.time(), record)
                if info.address:
                    break

            if info.address:
                address = '.'.join(map(lambda n: str(n), info.address))
            elif info.server:
                address = info.server
            if address:
                self.addPrinterSignal.emit(str(name), address, info.properties)

        elif state_change == ServiceStateChange.Removed:
            self.removePrinterSignal.emit(str(name))
