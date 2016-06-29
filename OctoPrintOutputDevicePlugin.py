from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from . import OctoPrintOutputDevice

from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange
from UM.Signal import Signal, signalemitter
from UM.Application import Application


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
        Application.getInstance().globalContainerStackChanged.connect(self.reCheckConnections)

    addPrinterSignal = Signal()

    ##  Start looking for devices on network.
    def start(self):
        self._browser = ServiceBrowser(self._zero_conf, u'_octoprint._tcp.local.', [self._onServiceChanged])

    ##  Stop looking for devices on network.
    def stop(self):
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
            printer.setApiKey(global_container_stack.getMetaDataEntry("octoprint_api_key"), "")
            printer.connectionStateChanged.connect(self._onPrinterConnectionStateChanged)
            printer.connect()

    ##  Handler for when the connection state of one of the detected printers changes
    def _onPrinterConnectionStateChanged(self, key):
        if self._printers[key].isConnected():
            self.getOutputDeviceManager().addOutputDevice(self._printers[key])
        else:
            self.getOutputDeviceManager().removeOutputDevice(key)

    ##  Handler for zeroConf detection
    def _onServiceChanged(self, zeroconf, service_type, name, state_change):
        if state_change == ServiceStateChange.Added:
            info = zeroconf.get_service_info(service_type, name)
            if info:
                address = '.'.join(map(lambda n: str(n), info.address))
                self.addPrinterSignal.emit(str(name), address, info.properties)

        elif state_change == ServiceStateChange.Removed:
            pass
            # TODO; This isn't testable right now. We need to also decide how to handle
            #