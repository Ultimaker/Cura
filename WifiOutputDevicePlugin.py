from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from . import WifiConnection

from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange
from UM.Signal import Signal, SignalEmitter

class WifiOutputDevicePlugin(OutputDevicePlugin, SignalEmitter):
    def __init__(self):
        super().__init__()
        self._zero_conf = Zeroconf()
        self._browser = None
        self._connections = {}
        self.addConnectionSignal.connect(self.addConnection) #Because the model needs to be created in the same thread as the QMLEngine, we use a signal.

    addConnectionSignal = Signal()

    ##  Start looking for devices on network.
    def start(self):
        self._browser = ServiceBrowser(Zeroconf(), u'_ultimaker._tcp.local.', [self._onServiceChanged])

    ##  Stop looking for devices on network.
    def stop(self):
        self._zero_conf.close()

    ##  Because the model needs to be created in the same thread as the QMLEngine, we use a signal.
    def addConnection(self, name, address, properties):
        if address == "10.180.1.30": #DEBUG
            connection = WifiConnection.WifiConnection(address, properties)
            connection.connect()
            self._connections[address] = connection
            connection.connectionStateChanged.connect(self._onPrinterConnectionStateChanged)

    def _onPrinterConnectionStateChanged(self, address):
        if self._connections[address].isConnected():
            self.getOutputDeviceManager().addOutputDevice(self._connections[address])
        else:
            self.getOutputDeviceManager().removeOutputDevice(self._connections[address])

    def removeConnection(self):
        pass

    def _onServiceChanged(self, zeroconf, service_type, name, state_change):
        if state_change == ServiceStateChange.Added:
            info = zeroconf.get_service_info(service_type, name)
            if info:
                if info.properties.get(b"type", None):
                    address = '.'.join(map(lambda n: str(n), info.address))
                    self.addConnectionSignal.emit(str(name), address, info.properties)

        elif state_change == ServiceStateChange.Removed:
            info = zeroconf.get_service_info(service_type, name)
            address = '.'.join(map(lambda n: str(n), info.address))
