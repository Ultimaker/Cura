# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Callable, Dict, List, Optional, TYPE_CHECKING

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject

from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Util import parseBool

if TYPE_CHECKING:
    from PyQt5.QtCore import QObject

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

    machineTypeChanged = pyqtSignal()

    @pyqtProperty(str, notify = machineTypeChanged)
    def machineType(self) -> str:
        return self._machine_type

    def setMachineType(self, machine_type: str) -> None:
        if self._machine_type != machine_type:
            self._machine_type = machine_type
            self.machineTypeChanged.emit()

    # Human readable machine type string
    @pyqtProperty(str, notify = machineTypeChanged)
    def readableMachineType(self) -> str:
        from cura.CuraApplication import CuraApplication
        machine_manager = CuraApplication.getInstance().getMachineManager()
        # In ClusterUM3OutputDevice, when it updates a printer information, it updates the machine type using the field
        # "machine_variant", and for some reason, it's not the machine type ID/codename/... but a human-readable string
        # like "Ultimaker 3". The code below handles this case.
        if machine_manager.hasMachineTypeName(self._machine_type):
            readable_type = self._machine_type
        else:
            readable_type = machine_manager.getMachineTypeNameFromId(self._machine_type)
            if not readable_type:
                readable_type = catalog.i18nc("@label", "Unknown")
        return readable_type

    @pyqtProperty(bool, notify = machineTypeChanged)
    def isUnknownMachineType(self) -> bool:
        from cura.CuraApplication import CuraApplication
        machine_manager = CuraApplication.getInstance().getMachineManager()
        if machine_manager.hasMachineTypeName(self._machine_type):
            readable_type = self._machine_type
        else:
            readable_type = machine_manager.getMachineTypeNameFromId(self._machine_type)
        return not readable_type

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

    def __init__(self, parent: Optional["QObject"] = None) -> None:
        super().__init__(parent)

        self._discovered_printer_by_ip_dict = dict()  # type: Dict[str, DiscoveredPrinter]

    discoveredPrintersChanged = pyqtSignal()

    @pyqtProperty(list, notify = discoveredPrintersChanged)
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

    @pyqtSlot(str)
    def createMachineFromDiscoveredPrinterAddress(self, ip_address: str) -> None:
        if ip_address not in self._discovered_printer_by_ip_dict:
            Logger.log("i", "Key [%s] does not exist in the discovered printers list.", ip_address)
            return

        self.createMachineFromDiscoveredPrinter(self._discovered_printer_by_ip_dict[ip_address])
