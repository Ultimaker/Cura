from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from . import NetworkPrinterOutputDevice

from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange
from UM.Signal import Signal, SignalEmitter
from UM.Application import Application

class WifiOutputDevicePlugin(OutputDevicePlugin, SignalEmitter):
    def __init__(self):
        super().__init__()
        self._zero_conf = Zeroconf()
        self._browser = None
        self._connections = {}
        self.addConnectionSignal.connect(self.addConnection) #Because the model needs to be created in the same thread as the QMLEngine, we use a signal.
        Application.getInstance().getMachineManager().activeMachineInstanceChanged.connect(self._onActiveMachineInstanceChanged)
    addConnectionSignal = Signal()

    ##  Start looking for devices on network.
    def start(self):
        self._browser = ServiceBrowser(Zeroconf(), u'_ultimaker._tcp.local.', [self._onServiceChanged])

    ##  Stop looking for devices on network.
    def stop(self):
        self._zero_conf.close()

    def _onActiveMachineInstanceChanged(self):
        active_machine_key = Application.getInstance().getMachineManager().getActiveMachineInstance().getKey()
        for address in self._connections:
            if self._connections[address].getKey() == active_machine_key:
                self._connections[address].connect()
                self._connections[address].connectionStateChanged.connect(self._onPrinterConnectionStateChanged)
            else:
                self._connections[address].close()
        print("on active machine instance changed" , active_machine_key)

    ##  Because the model needs to be created in the same thread as the QMLEngine, we use a signal.
    def addConnection(self, name, address, properties):
        connection = NetworkPrinterOutputDevice.NetworkPrinterOutputDevice(name, address, properties)
        self._connections[address] = connection
        if connection.getKey() == Application.getInstance().getMachineManager().getActiveMachineInstance().getKey():
            self._connections[address].connect()
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
            if info:
                address = '.'.join(map(lambda n: str(n), info.address))
