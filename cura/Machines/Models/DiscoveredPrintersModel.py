from typing import Callable, List, Optional, TYPE_CHECKING

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject

from UM.Logger import Logger

if TYPE_CHECKING:
    from PyQt5.QtCore import QObject


class DiscoveredPrinter(QObject):

    def __init__(self, ip_address: str, key: str, name: str, create_callback: Callable[[str], None], machine_type: str,
                 device, parent = None) -> None:
        super().__init__(parent)
        self._ip_address = ip_address
        self._key = key
        self._name = name
        self._create_callback = create_callback
        self._machine_type = machine_type
        self._device = device

    nameChanged = pyqtSignal()

    @pyqtProperty(str, notify = nameChanged)
    def name(self) -> str:
        return self._name

    def setName(self, name: str) -> None:
        if self._name != name:
            self._name = name
            self.nameChanged.emit()

    machineTypeChanged = pyqtSignal()

    @pyqtProperty(str, notify = machineTypeChanged)
    def machine_type(self) -> str:
        return self._machine_type

    def setMachineType(self, machine_type: str) -> None:
        if self._machine_type != machine_type:
            self._machine_type = machine_type
            self.machineTypeChanged.emit()

    @pyqtProperty(QObject, constant = True)
    def device(self):
        return self._device


#
# Discovered printers are all the printers that were found on the network, which provide a more convenient way
# to add networked printers (Plugin finds a bunch of printers, user can select one from the list, plugin can then
# add that printer to Cura as the active one).
#
class DiscoveredPrinterModel(QObject):

    def __init__(self, parent: Optional["QObject"]) -> None:
        super().__init__(parent)

        self._discovered_printer_dict = dict()

    discoveredPrintersChanged = pyqtSignal()

    @pyqtProperty(list, notify = discoveredPrintersChanged)
    def discovered_printers(self) -> "List[DiscoveredPrinter]":
        item_list = list(x for x in self._discovered_printer_dict.values())
        item_list.sort(key = lambda x: x.name)
        return item_list

    def addDiscoveredPrinter(self, ip_address: str, key: str, name: str, create_callback: Callable[[str], None],
                             machine_type: str, device) -> None:
        if ip_address in self._discovered_printer_dict:
            Logger.log("e", "Printer with ip [%s] has already been added", ip_address)
            return

        discovered_printer = DiscoveredPrinter(ip_address, key, name, create_callback, machine_type, device, parent = self)
        self._discovered_printer_dict[ip_address] = discovered_printer
        self.discoveredPrintersChanged.emit()

    def updateDiscoveredPrinter(self, ip_address: str,
                                name: Optional[str] = None,
                                machine_type: Optional[str] = None) -> None:
        if ip_address not in self._discovered_printer_dict:
            Logger.log("e", "Printer with ip [%s] is not known", ip_address)
            return

        item = self._discovered_printer_dict[ip_address]

        if name is not None:
            item.setName(name)
        if machine_type is not None:
            item.setMachineType(machine_type)

    def removeDiscoveredPrinter(self, ip_address: str) -> None:
        if ip_address not in self._discovered_printer_dict:
            Logger.log("i", "Key [%s] does not exist in the discovered printers list.", ip_address)
            return

        del self._discovered_printer_dict[ip_address]
        self.discoveredPrintersChanged.emit()

    @pyqtSlot("QVariant")
    def createMachineFromDiscoveredPrinter(self, discovered_printer: "DiscoveredPrinter") -> None:
        discovered_printer.create_callback()
