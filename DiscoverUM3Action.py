from cura.MachineAction import MachineAction

from UM.Application import Application

from PyQt5.QtCore import pyqtSignal, pyqtProperty, pyqtSlot

class DiscoverUM3Action(MachineAction):
    def __init__(self):
        super().__init__("DiscoverUM3Action", "Discover printers")
        self._qml_url = "DiscoverUM3Action.qml"

        self._network_plugin = None

    printerDetected = pyqtSignal()

    @pyqtSlot()
    def startDiscovery(self):
        if not self._network_plugin:
            self._network_plugin = Application.getInstance().getOutputDeviceManager().getOutputDevicePlugin("JediWifiPrintingPlugin")
            self._network_plugin.addPrinterSignal.connect(self._onPrinterAdded)
            self.printerDetected.emit()

    def _onPrinterAdded(self, *args):
        self.printerDetected.emit()

    @pyqtProperty("QVariantList", notify = printerDetected)
    def foundDevices(self):
        if self._network_plugin:
            printers = self._network_plugin.getPrinters()
            return [printers[printer] for printer in printers]
        else:
            return []

    @pyqtSlot(str)
    def setKey(self, key):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            if "key" in global_container_stack.getMetaData():
                global_container_stack.setMetaDataEntry("key", key)
            else:
                global_container_stack.addMetaDataEntry("key", key)
