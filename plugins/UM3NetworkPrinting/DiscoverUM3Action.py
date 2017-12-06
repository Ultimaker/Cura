import os.path
import time

from PyQt5.QtCore import pyqtSignal, pyqtProperty, pyqtSlot, QObject

from UM.Application import Application
from UM.PluginRegistry import PluginRegistry
from UM.Logger import Logger
from UM.i18n import i18nCatalog

from cura.MachineAction import MachineAction

catalog = i18nCatalog("cura")

class DiscoverUM3Action(MachineAction):
    def __init__(self):
        super().__init__("DiscoverUM3Action", catalog.i18nc("@action","Connect via Network"))
        self._qml_url = "DiscoverUM3Action.qml"

        self._network_plugin = None

        self.__additional_components_context = None
        self.__additional_component = None
        self.__additional_components_view = None

        Application.getInstance().engineCreatedSignal.connect(self._createAdditionalComponentsView)

        self._last_zeroconf_event_time = time.time()
        self._zeroconf_change_grace_period = 0.25 # Time to wait after a zeroconf service change before allowing a zeroconf reset

    printersChanged = pyqtSignal()

    @pyqtSlot()
    def startDiscovery(self):
        if not self._network_plugin:
            Logger.log("d", "Starting printer discovery.")
            self._network_plugin = Application.getInstance().getOutputDeviceManager().getOutputDevicePlugin("UM3NetworkPrinting")
            self._network_plugin.printerListChanged.connect(self._onPrinterDiscoveryChanged)
            self.printersChanged.emit()

    ##  Re-filters the list of printers.
    @pyqtSlot()
    def reset(self):
        Logger.log("d", "Reset the list of found printers.")
        self.printersChanged.emit()

    @pyqtSlot()
    def restartDiscovery(self):
        # Ensure that there is a bit of time after a printer has been discovered.
        # This is a work around for an issue with Qt 5.5.1 up to Qt 5.7 which can segfault if we do this too often.
        # It's most likely that the QML engine is still creating delegates, where the python side already deleted or
        # garbage collected the data.
        # Whatever the case, waiting a bit ensures that it doesn't crash.
        if time.time() - self._last_zeroconf_event_time > self._zeroconf_change_grace_period:
            if not self._network_plugin:
                self.startDiscovery()
            else:
                self._network_plugin.startDiscovery()

    @pyqtSlot(str, str)
    def removeManualPrinter(self, key, address):
        if not self._network_plugin:
            return

        self._network_plugin.removeManualPrinter(key, address)

    @pyqtSlot(str, str)
    def setManualPrinter(self, key, address):
        if key != "":
            # This manual printer replaces a current manual printer
            self._network_plugin.removeManualPrinter(key)

        if address != "":
            self._network_plugin.addManualPrinter(address)

    def _onPrinterDiscoveryChanged(self, *args):
        self._last_zeroconf_event_time = time.time()
        self.printersChanged.emit()

    @pyqtProperty("QVariantList", notify = printersChanged)
    def foundDevices(self):
        if self._network_plugin:
            if Application.getInstance().getGlobalContainerStack():
                global_printer_type = Application.getInstance().getGlobalContainerStack().getBottom().getId()
            else:
                global_printer_type = "unknown"

            printers = list(self._network_plugin.getPrinters().values())
            # TODO; There are still some testing printers that don't have a correct printer type, so don't filter out unkown ones just yet.
            printers = [printer for printer in printers if printer.printerType == global_printer_type or printer.printerType == "unknown"]
            printers.sort(key = lambda k: k.name)
            return printers
        else:
            return []

    @pyqtSlot(str)
    def setKey(self, key):
        Logger.log("d", "Attempting to set the network key of the active machine to %s", key)
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "um_network_key" in meta_data:
                global_container_stack.setMetaDataEntry("um_network_key", key)
                # Delete old authentication data.
                Logger.log("d", "Removing old authentication id %s for device %s", global_container_stack.getMetaDataEntry("network_authentication_id", None), key)
                global_container_stack.removeMetaDataEntry("network_authentication_id")
                global_container_stack.removeMetaDataEntry("network_authentication_key")
            else:
                global_container_stack.addMetaDataEntry("um_network_key", key)

        if self._network_plugin:
            # Ensure that the connection states are refreshed.
            self._network_plugin.reCheckConnections()

    @pyqtSlot(result = str)
    def getStoredKey(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "um_network_key" in meta_data:
                return global_container_stack.getMetaDataEntry("um_network_key")

        return ""

    @pyqtSlot()
    def loadConfigurationFromPrinter(self):
        machine_manager = Application.getInstance().getMachineManager()
        hotend_ids = machine_manager.printerOutputDevices[0].hotendIds
        for index in range(len(hotend_ids)):
            machine_manager.printerOutputDevices[0].hotendIdChanged.emit(index, hotend_ids[index])
        material_ids = machine_manager.printerOutputDevices[0].materialIds
        for index in range(len(material_ids)):
            machine_manager.printerOutputDevices[0].materialIdChanged.emit(index, material_ids[index])

    def _createAdditionalComponentsView(self):
        Logger.log("d", "Creating additional ui components for UM3.")

        # Create networking dialog
        path = os.path.join(PluginRegistry.getInstance().getPluginPath("UM3NetworkPrinting"), "UM3InfoComponents.qml")
        self.__additional_components_view = Application.getInstance().createQmlComponent(path, {"manager": self})
        if not self.__additional_components_view:
            Logger.log("w", "Could not create ui components for UM3.")
            return

        # Create extra components
        Application.getInstance().addAdditionalComponent("monitorButtons", self.__additional_components_view.findChild(QObject, "networkPrinterConnectButton"))
        Application.getInstance().addAdditionalComponent("machinesDetailPane", self.__additional_components_view.findChild(QObject, "networkPrinterConnectionInfo"))
