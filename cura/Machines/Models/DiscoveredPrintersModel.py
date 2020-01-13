# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Callable, Dict, List, Optional, TYPE_CHECKING

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, QTimer

from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Util import parseBool
from UM.OutputDevice.OutputDeviceManager import ManualDeviceAdditionAttempt

if TYPE_CHECKING:
    from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
    from cura.CuraApplication import CuraApplication
    from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice


catalog = i18nCatalog("cura")


class DiscoveredPrinter(QObject):

    def __init__(self, ip_address: str, key: str, name: str, create_callback: Callable[[str], None], machine_type: str,
                 device: "NetworkedPrinterOutputDevice", parent: Optional["QObject"] = None) -> None:
        super().__init__(parent)

        self._ip_address = ip_address
        self._key = key
        self._name = name
        self.create_callback = create_callback
        self._machine_type = machine_type
        self._device = device

    nameChanged = pyqtSignal()

    def getKey(self) -> str:
        return self._key

    @pyqtProperty(str, notify = nameChanged)
    def name(self) -> str:
        return self._name

    def setName(self, name: str) -> None:
        if self._name != name:
            self._name = name
            self.nameChanged.emit()

    @pyqtProperty(str, constant = True)
    def address(self) -> str:
        return self._ip_address

    machineTypeChanged = pyqtSignal()

    @pyqtProperty(str, notify = machineTypeChanged)
    def machineType(self) -> str:
        return self._machine_type

    def setMachineType(self, machine_type: str) -> None:
        if self._machine_type != machine_type:
            self._machine_type = machine_type
            self.machineTypeChanged.emit()

    # Checks if the given machine type name in the available machine list.
    # The machine type is a code name such as "ultimaker_3", while the machine type name is the human-readable name of
    # the machine type, which is "Ultimaker 3" for "ultimaker_3".
    def _hasHumanReadableMachineTypeName(self, machine_type_name: str) -> bool:
        from cura.CuraApplication import CuraApplication
        results = CuraApplication.getInstance().getContainerRegistry().findDefinitionContainersMetadata(name = machine_type_name)
        return len(results) > 0

    # Human readable machine type string
    @pyqtProperty(str, notify = machineTypeChanged)
    def readableMachineType(self) -> str:
        from cura.CuraApplication import CuraApplication
        machine_manager = CuraApplication.getInstance().getMachineManager()
        # In NetworkOutputDevice, when it updates a printer information, it updates the machine type using the field
        # "machine_variant", and for some reason, it's not the machine type ID/codename/... but a human-readable string
        # like "Ultimaker 3". The code below handles this case.
        if self._hasHumanReadableMachineTypeName(self._machine_type):
            readable_type = self._machine_type
        else:
            readable_type = self._getMachineTypeNameFromId(self._machine_type)
            if not readable_type:
                readable_type = catalog.i18nc("@label", "Unknown")
        return readable_type

    @pyqtProperty(bool, notify = machineTypeChanged)
    def isUnknownMachineType(self) -> bool:
        if self._hasHumanReadableMachineTypeName(self._machine_type):
            readable_type = self._machine_type
        else:
            readable_type = self._getMachineTypeNameFromId(self._machine_type)
        return not readable_type

    def _getMachineTypeNameFromId(self, machine_type_id: str) -> str:
        machine_type_name = ""
        from cura.CuraApplication import CuraApplication
        results = CuraApplication.getInstance().getContainerRegistry().findDefinitionContainersMetadata(id = machine_type_id)
        if results:
            machine_type_name = results[0]["name"]
        return machine_type_name

    @pyqtProperty(QObject, constant = True)
    def device(self) -> "NetworkedPrinterOutputDevice":
        return self._device

    @pyqtProperty(bool, constant = True)
    def isHostOfGroup(self) -> bool:
        return getattr(self._device, "clusterSize", 1) > 0

    @pyqtProperty(str, constant = True)
    def sectionName(self) -> str:
        if self.isUnknownMachineType or not self.isHostOfGroup:
            return catalog.i18nc("@label", "The printer(s) below cannot be connected because they are part of a group")
        else:
            return catalog.i18nc("@label", "Available networked printers")


#
# Discovered printers are all the printers that were found on the network, which provide a more convenient way
# to add networked printers (Plugin finds a bunch of printers, user can select one from the list, plugin can then
# add that printer to Cura as the active one).
#
class DiscoveredPrintersModel(QObject):

    def __init__(self, application: "CuraApplication", parent: Optional["QObject"] = None) -> None:
        super().__init__(parent)

        self._application = application
        self._discovered_printer_by_ip_dict = dict()  # type: Dict[str, DiscoveredPrinter]

        self._plugin_for_manual_device = None  # type: Optional[OutputDevicePlugin]
        self._manual_device_address = ""

        self._manual_device_request_timeout_in_seconds = 5  # timeout for adding a manual device in seconds
        self._manual_device_request_timer = QTimer()
        self._manual_device_request_timer.setInterval(self._manual_device_request_timeout_in_seconds * 1000)
        self._manual_device_request_timer.setSingleShot(True)
        self._manual_device_request_timer.timeout.connect(self._onManualRequestTimeout)

    discoveredPrintersChanged = pyqtSignal()

    @pyqtSlot(str)
    def checkManualDevice(self, address: str) -> None:
        if self.hasManualDeviceRequestInProgress:
            Logger.log("i", "A manual device request for address [%s] is still in progress, do nothing",
                       self._manual_device_address)
            return

        priority_order = [
            ManualDeviceAdditionAttempt.PRIORITY,
            ManualDeviceAdditionAttempt.POSSIBLE,
        ]  # type: List[ManualDeviceAdditionAttempt]

        all_plugins_dict = self._application.getOutputDeviceManager().getAllOutputDevicePlugins()

        can_add_manual_plugins = [item for item in filter(
            lambda plugin_item: plugin_item.canAddManualDevice(address) in priority_order,
            all_plugins_dict.values())]

        if not can_add_manual_plugins:
            Logger.log("d", "Could not find a plugin to accept adding %s manually via address.", address)
            return

        plugin = max(can_add_manual_plugins, key = lambda p: priority_order.index(p.canAddManualDevice(address)))
        self._plugin_for_manual_device = plugin
        self._plugin_for_manual_device.addManualDevice(address, callback = self._onManualDeviceRequestFinished)
        self._manual_device_address = address
        self._manual_device_request_timer.start()
        self.hasManualDeviceRequestInProgressChanged.emit()

    @pyqtSlot()
    def cancelCurrentManualDeviceRequest(self) -> None:
        self._manual_device_request_timer.stop()

        if self._manual_device_address:
            if self._plugin_for_manual_device is not None:
                self._plugin_for_manual_device.removeManualDevice(self._manual_device_address, address = self._manual_device_address)
            self._manual_device_address = ""
            self._plugin_for_manual_device = None
            self.hasManualDeviceRequestInProgressChanged.emit()
            self.manualDeviceRequestFinished.emit(False)

    def _onManualRequestTimeout(self) -> None:
        Logger.log("w", "Manual printer [%s] request timed out. Cancel the current request.", self._manual_device_address)
        self.cancelCurrentManualDeviceRequest()

    hasManualDeviceRequestInProgressChanged = pyqtSignal()

    @pyqtProperty(bool, notify = hasManualDeviceRequestInProgressChanged)
    def hasManualDeviceRequestInProgress(self) -> bool:
        return self._manual_device_address != ""

    manualDeviceRequestFinished = pyqtSignal(bool, arguments = ["success"])

    def _onManualDeviceRequestFinished(self, success: bool, address: str) -> None:
        self._manual_device_request_timer.stop()
        if address == self._manual_device_address:
            self._manual_device_address = ""
            self.hasManualDeviceRequestInProgressChanged.emit()
            self.manualDeviceRequestFinished.emit(success)

    @pyqtProperty("QVariantMap", notify = discoveredPrintersChanged)
    def discoveredPrintersByAddress(self) -> Dict[str, DiscoveredPrinter]:
        return self._discovered_printer_by_ip_dict
    
    @pyqtProperty("QVariantList", notify = discoveredPrintersChanged)
    def discoveredPrinters(self) -> List["DiscoveredPrinter"]:
        item_list = list(
            x for x in self._discovered_printer_by_ip_dict.values() if not parseBool(x.device.getProperty("temporary")))

        # Split the printers into 2 lists and sort them ascending based on names.
        available_list = []
        not_available_list = []
        for item in item_list:
            if item.isUnknownMachineType or getattr(item.device, "clusterSize", 1) < 1:
                not_available_list.append(item)
            else:
                available_list.append(item)

        available_list.sort(key = lambda x: x.device.name)
        not_available_list.sort(key = lambda x: x.device.name)

        return available_list + not_available_list

    def addDiscoveredPrinter(self, ip_address: str, key: str, name: str, create_callback: Callable[[str], None],
                             machine_type: str, device: "NetworkedPrinterOutputDevice") -> None:
        if ip_address in self._discovered_printer_by_ip_dict:
            Logger.log("e", "Printer with ip [%s] has already been added", ip_address)
            return

        discovered_printer = DiscoveredPrinter(ip_address, key, name, create_callback, machine_type, device, parent = self)
        self._discovered_printer_by_ip_dict[ip_address] = discovered_printer
        self.discoveredPrintersChanged.emit()

    def updateDiscoveredPrinter(self, ip_address: str,
                                name: Optional[str] = None,
                                machine_type: Optional[str] = None) -> None:
        if ip_address not in self._discovered_printer_by_ip_dict:
            Logger.log("w", "Printer with ip [%s] is not known", ip_address)
            return

        item = self._discovered_printer_by_ip_dict[ip_address]

        if name is not None:
            item.setName(name)
        if machine_type is not None:
            item.setMachineType(machine_type)

    def removeDiscoveredPrinter(self, ip_address: str) -> None:
        if ip_address not in self._discovered_printer_by_ip_dict:
            Logger.log("w", "Key [%s] does not exist in the discovered printers list.", ip_address)
            return

        del self._discovered_printer_by_ip_dict[ip_address]
        self.discoveredPrintersChanged.emit()

    # A convenience function for QML to create a machine (GlobalStack) out of the given discovered printer.
    # This function invokes the given discovered printer's "create_callback" to do this.
    @pyqtSlot("QVariant")
    def createMachineFromDiscoveredPrinter(self, discovered_printer: "DiscoveredPrinter") -> None:
        discovered_printer.create_callback(discovered_printer.getKey())
