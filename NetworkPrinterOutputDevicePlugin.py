from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from . import NetworkPrinterOutputDevice

from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange
from UM.Signal import Signal, signalemitter
from UM.Application import Application


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

        # Because the model needs to be created in the same thread as the QMLEngine, we use a signal.
        self.addPrinterSignal.connect(self.addPrinter)
        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalStackChanged)

    addPrinterSignal = Signal()

    ##  Start looking for devices on network.
    def start(self):
        self._browser = ServiceBrowser(self._zero_conf, u'_ultimaker._tcp.local.', [self._onServiceChanged])

    ##  Stop looking for devices on network.
    def stop(self):
        self._zero_conf.close()

    def _onGlobalStackChanged(self):
        active_machine = Application.getInstance().getGlobalContainerStack()
        if not active_machine:
            return

        for key in self._printers:
            if key == active_machine.getMetaDataEntry("key"):
                self._printers[key].connect()
                self._printers[key].connectionStateChanged.connect(self._onPrinterConnectionStateChanged)
            else:
                self._printers[key].close()

    ##  Because the model needs to be created in the same thread as the QMLEngine, we use a signal.
    def addPrinter(self, name, address, properties):
        printer = NetworkPrinterOutputDevice.NetworkPrinterOutputDevice(name, address, properties)
        self._printers[printer.getKey()] = printer
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack and printer.getKey() == global_container_stack.getMetaDataEntry("key"):
            self._printers[printer.getKey()].connect()
            printer.connectionStateChanged.connect(self._onPrinterConnectionStateChanged)

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
                if info.properties.get(b"type", None):
                    address = '.'.join(map(lambda n: str(n), info.address))
                    self.addPrinterSignal.emit(str(name), address, info.properties)

        elif state_change == ServiceStateChange.Removed:
            pass
            # TODO; This isn't testable right now. We need to also decide how to handle
            #