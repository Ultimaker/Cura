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
    discoveredDevicesChanged = pyqtSignal()

    def __init__(self):
        super().__init__("DiscoverUM3Action", catalog.i18nc("@action","Connect via Network"))
        self._qml_url = "DiscoverUM3Action.qml"

        self._network_plugin = None

        self.__additional_components_context = None
        self.__additional_component = None
        self.__additional_components_view = None

        Application.getInstance().engineCreatedSignal.connect(self._createAdditionalComponentsView)

        self._last_zero_conf_event_time = time.time()

        # Time to wait after a zero-conf service change before allowing a zeroconf reset
        self._zero_conf_change_grace_period = 0.25

    @pyqtSlot()
    def startDiscovery(self):
        if not self._network_plugin:
            Logger.log("d", "Starting device discovery.")
            self._network_plugin = Application.getInstance().getOutputDeviceManager().getOutputDevicePlugin("UM3NetworkPrinting")
            self._network_plugin.discoveredDevicesChanged.connect(self._onDeviceDiscoveryChanged)
            self.discoveredDevicesChanged.emit()

    ##  Re-filters the list of devices.
    @pyqtSlot()
    def reset(self):
        Logger.log("d", "Reset the list of found devices.")
        if self._network_plugin:
            self._network_plugin.resetLastManualDevice()
        self.discoveredDevicesChanged.emit()

    @pyqtSlot()
    def restartDiscovery(self):
        # Ensure that there is a bit of time after a printer has been discovered.
        # This is a work around for an issue with Qt 5.5.1 up to Qt 5.7 which can segfault if we do this too often.
        # It's most likely that the QML engine is still creating delegates, where the python side already deleted or
        # garbage collected the data.
        # Whatever the case, waiting a bit ensures that it doesn't crash.
        if time.time() - self._last_zero_conf_event_time > self._zero_conf_change_grace_period:
            if not self._network_plugin:
                self.startDiscovery()
            else:
                self._network_plugin.startDiscovery()

    @pyqtSlot(str, str)
    def removeManualDevice(self, key, address):
        if not self._network_plugin:
            return

        self._network_plugin.removeManualDevice(key, address)

    @pyqtSlot(str, str)
    def setManualDevice(self, key, address):
        if key != "":
            # This manual printer replaces a current manual printer
            self._network_plugin.removeManualDevice(key)

        if address != "":
            self._network_plugin.addManualDevice(address)

    def _onDeviceDiscoveryChanged(self, *args):
        self._last_zero_conf_event_time = time.time()
        self.discoveredDevicesChanged.emit()

    @pyqtProperty("QVariantList", notify = discoveredDevicesChanged)
    def foundDevices(self):
        if self._network_plugin:

            printers = list(self._network_plugin.getDiscoveredDevices().values())
            printers.sort(key = lambda k: k.name)
            return printers
        else:
            return []

    @pyqtSlot(str)
    def setGroupName(self, group_name):
        Logger.log("d", "Attempting to set the group name of the active machine to %s", group_name)
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "connect_group_name" in meta_data:
                previous_connect_group_name = meta_data["connect_group_name"]
                global_container_stack.setMetaDataEntry("connect_group_name", group_name)
                # Find all the places where there is the same group name and change it accordingly
                Application.getInstance().getMachineManager().replaceContainersMetadata(key = "connect_group_name", value = previous_connect_group_name, new_value = group_name)
            else:
                global_container_stack.addMetaDataEntry("connect_group_name", group_name)
                global_container_stack.addMetaDataEntry("hidden", False)

        if self._network_plugin:
            # Ensure that the connection states are refreshed.
            self._network_plugin.reCheckConnections()

    @pyqtSlot(str)
    def setKey(self, key):
        Logger.log("d", "Attempting to set the network key of the active machine to %s", key)
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "um_network_key" in meta_data:
                previous_network_key= meta_data["um_network_key"]
                global_container_stack.setMetaDataEntry("um_network_key", key)
                # Delete old authentication data.
                Logger.log("d", "Removing old authentication id %s for device %s", global_container_stack.getMetaDataEntry("network_authentication_id", None), key)
                global_container_stack.removeMetaDataEntry("network_authentication_id")
                global_container_stack.removeMetaDataEntry("network_authentication_key")
                Application.getInstance().getMachineManager().replaceContainersMetadata(key = "um_network_key", value = previous_network_key, new_value = key)
            else:
                global_container_stack.addMetaDataEntry("um_network_key", key)

        if self._network_plugin:
            # Ensure that the connection states are refreshed.
            self._network_plugin.reCheckConnections()

    @pyqtSlot(result = str)
    def getStoredKey(self) -> str:
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            meta_data = global_container_stack.getMetaData()
            if "um_network_key" in meta_data:
                return global_container_stack.getMetaDataEntry("um_network_key")

        return ""

    @pyqtSlot(result = str)
    def getLastManualEntryKey(self) -> str:
        if self._network_plugin:
            return self._network_plugin.getLastManualDevice()
        return ""

    @pyqtSlot(str, result = bool)
    def existsKey(self, key) -> bool:
        return Application.getInstance().getMachineManager().existNetworkInstances(network_key = key)

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
