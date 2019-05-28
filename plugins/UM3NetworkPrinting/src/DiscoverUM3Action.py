# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os.path
import time
from typing import Optional, TYPE_CHECKING

from PyQt5.QtCore import pyqtSignal, pyqtProperty, pyqtSlot, QObject

from UM.PluginRegistry import PluginRegistry
from UM.Logger import Logger
from UM.i18n import i18nCatalog

from cura.CuraApplication import CuraApplication
from cura.MachineAction import MachineAction
from cura.Settings.CuraContainerRegistry import CuraContainerRegistry

from .UM3OutputDevicePlugin import UM3OutputDevicePlugin

if TYPE_CHECKING:
    from cura.PrinterOutput.PrinterOutputDevice import PrinterOutputDevice

catalog = i18nCatalog("cura")


class DiscoverUM3Action(MachineAction):
    discoveredDevicesChanged = pyqtSignal()

    def __init__(self) -> None:
        super().__init__("DiscoverUM3Action", catalog.i18nc("@action","Connect via Network"))
        self._qml_url = "resources/qml/DiscoverUM3Action.qml"

        self._network_plugin = None #type: Optional[UM3OutputDevicePlugin]

        self.__additional_components_view = None #type: Optional[QObject]

        CuraApplication.getInstance().engineCreatedSignal.connect(self._createAdditionalComponentsView)

        self._last_zero_conf_event_time = time.time() #type: float

        # Time to wait after a zero-conf service change before allowing a zeroconf reset
        self._zero_conf_change_grace_period = 0.25 #type: float

    # Overrides the one in MachineAction.
    # This requires not attention from the user (any more), so we don't need to show any 'upgrade screens'.
    def needsUserInteraction(self) -> bool:
        return False

    @pyqtSlot()
    def startDiscovery(self):
        if not self._network_plugin:
            Logger.log("d", "Starting device discovery.")
            self._network_plugin = CuraApplication.getInstance().getOutputDeviceManager().getOutputDevicePlugin("UM3NetworkPrinting")
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
    def setGroupName(self, group_name: str) -> None:
        Logger.log("d", "Attempting to set the group name of the active machine to %s", group_name)
        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()
        if global_container_stack:
            # Update a GlobalStacks in the same group with the new group name.
            group_id = global_container_stack.getMetaDataEntry("group_id")
            machine_manager = CuraApplication.getInstance().getMachineManager()
            for machine in machine_manager.getMachinesInGroup(group_id):
                machine.setMetaDataEntry("group_name", group_name)

            # Set the default value for "hidden", which is used when you have a group with multiple types of printers
            global_container_stack.setMetaDataEntry("hidden", False)

        if self._network_plugin:
            # Ensure that the connection states are refreshed.
            self._network_plugin.refreshConnections()

    # Associates the currently active machine with the given printer device. The network connection information will be
    # stored into the metadata of the currently active machine.
    @pyqtSlot(QObject)
    def associateActiveMachineWithPrinterDevice(self, printer_device: Optional["PrinterOutputDevice"]) -> None:
        if self._network_plugin:
            self._network_plugin.associateActiveMachineWithPrinterDevice(printer_device)

    @pyqtSlot(result = str)
    def getStoredKey(self) -> str:
        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()
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
    def existsKey(self, key: str) -> bool:
        metadata_filter = {"um_network_key": key}
        containers = CuraContainerRegistry.getInstance().findContainerStacks(type="machine", **metadata_filter)
        return bool(containers)

    @pyqtSlot()
    def loadConfigurationFromPrinter(self) -> None:
        machine_manager = CuraApplication.getInstance().getMachineManager()
        hotend_ids = machine_manager.printerOutputDevices[0].hotendIds
        for index in range(len(hotend_ids)):
            machine_manager.printerOutputDevices[0].hotendIdChanged.emit(index, hotend_ids[index])
        material_ids = machine_manager.printerOutputDevices[0].materialIds
        for index in range(len(material_ids)):
            machine_manager.printerOutputDevices[0].materialIdChanged.emit(index, material_ids[index])

    def _createAdditionalComponentsView(self) -> None:
        Logger.log("d", "Creating additional ui components for UM3.")

        # Create networking dialog
        plugin_path = PluginRegistry.getInstance().getPluginPath("UM3NetworkPrinting")
        if not plugin_path:
            return
        path = os.path.join(plugin_path, "resources/qml/UM3InfoComponents.qml")
        self.__additional_components_view = CuraApplication.getInstance().createQmlComponent(path, {"manager": self})
        if not self.__additional_components_view:
            Logger.log("w", "Could not create ui components for UM3.")
            return

        # Create extra components
        CuraApplication.getInstance().addAdditionalComponent("monitorButtons", self.__additional_components_view.findChild(QObject, "networkPrinterConnectButton"))
