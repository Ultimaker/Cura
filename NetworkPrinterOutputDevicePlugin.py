from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from . import NetworkPrinterOutputDevice

from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange
from UM.Signal import Signal, SignalEmitter
from UM.Application import Application


class NetworkPrinterOutputDevicePlugin(OutputDevicePlugin, SignalEmitter):
    def __init__(self):
        super().__init__()
        self._zero_conf = Zeroconf()
        self._browser = None
        self._printers = {}

        # Because the model needs to be created in the same thread as the QMLEngine, we use a signal.
        self.addPrinterSignal.connect(self.addPrinter)
        Application.getInstance().getMachineManager().activeMachineInstanceChanged.connect(self._onActiveMachineInstanceChanged)

    addPrinterSignal = Signal()

    ##  Start looking for devices on network.
    def start(self):
        self._browser = ServiceBrowser(self._zero_conf, u'_ultimaker._tcp.local.', [self._onServiceChanged])

    ##  Stop looking for devices on network.s
    def stop(self):
        self._zero_conf.close()

    def _onActiveMachineInstanceChanged(self):
        active_machine_key = Application.getInstance().getMachineManager().getActiveMachineInstance().getKey()
        for key in self._printers:
            if key == active_machine_key:
                self._printers[key].connect()
                self._printers[key].connectionStateChanged.connect(self._onPrinterConnectionStateChanged)
            else:
                self._printers[key].close()

    ##  Because the model needs to be created in the same thread as the QMLEngine, we use a signal.
    def addPrinter(self, name, address, properties):
        printer = NetworkPrinterOutputDevice.NetworkPrinterOutputDevice(name, address, properties)
        self._printers[printer.getKey()] = printer
        if printer.getKey() == Application.getInstance().getMachineManager().getActiveMachineInstance().getKey():
            self._printers[printer.getKey()].connect()
        printer.connectionStateChanged.connect(self._onPrinterConnectionStateChanged)

    def _onPrinterConnectionStateChanged(self, key):
        if self._printers[key].isConnected():
            self.getOutputDeviceManager().addOutputDevice(self._printers[key])
        else:
            self.getOutputDeviceManager().removeOutputDevice(self._printers[key])

    def removePrinter(self):
        pass

    def _onServiceChanged(self, zeroconf, service_type, name, state_change):
        if state_change == ServiceStateChange.Added:
            info = zeroconf.get_service_info(service_type, name)
            if info:
                if info.properties.get(b"type", None):
                    address = '.'.join(map(lambda n: str(n), info.address))
                    self.addPrinterSignal.emit(str(name), address, info.properties)

        elif state_change == ServiceStateChange.Removed:
            info = zeroconf.get_service_info(service_type, name)
            if info:
                address = '.'.join(map(lambda n: str(n), info.address))
