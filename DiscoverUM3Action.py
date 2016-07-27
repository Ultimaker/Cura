from cura.MachineAction import MachineAction

from UM.Application import Application

from PyQt5.QtCore import pyqtSignal, pyqtProperty, pyqtSlot

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

class DiscoverUM3Action(MachineAction):
    def __init__(self):
        super().__init__("DiscoverUM3Action", catalog.i18nc("@action","Connect via Network"))
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
            return list(printers.values())
        else:
            return []

    @pyqtSlot(str)
    def setKey(self, key):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "um_network_key" in meta_data:
                global_container_stack.setMetaDataEntry("um_network_key", key)
                # Delete old authentication data.
                global_container_stack.removeMetaDataEntry("network_authentication_id")
                global_container_stack.removeMetaDataEntry("network_authentication_key")
            else:
                global_container_stack.addMetaDataEntry("um_network_key", key)

        if self._network_plugin:
            # Ensure that the connection states are refreshed.
            self._network_plugin.reCheckConnections()
