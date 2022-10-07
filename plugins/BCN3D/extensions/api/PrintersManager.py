from PyQt6.QtCore import QObject, pyqtSlot

from UM.Scene.Selection import Selection
from cura.CuraApplication import CuraApplication

from  .AuthService import AuthService
from .DataService import DataService
from .Device import Device
from UM.Logger import Logger
from cura.Settings.CuraStackBuilder import CuraStackBuilder


class PrintersManager(QObject):
    def __init__(self):
        super().__init__()
        if PrintersManager.__instance is not None:
            raise ValueError("Duplicate singleton creation")
        self._cura_application = CuraApplication.getInstance()
        self._data_api_service = DataService.getInstance()
        self._application = CuraApplication.getInstance()
        AuthService.getInstance().authStateChanged.connect(self._authStateChanged)



    def _authStateChanged(self, logged_in):
        if logged_in:
            self._addPrinters()
        else:
            self._resetPrinters()


    def _addPrinters(self):
        printers = self._data_api_service.getPrinters()
        discovered_printers_model = self._cura_application.getDiscoveredPrintersModel()
        for printer in printers:
            discovered_printers_model.addDiscoveredPrinter(printer["serialnumber"], printer["serialnumber"], printer["printername"], self._createMachine, printer["printermodel"], Device(printer["printername"]))

    def _resetPrinters(self):
        discovered_printers_model = self._cura_application.getDiscoveredPrintersModel()
        discovered_printers = discovered_printers_model.discoveredPrinters
        for printer in discovered_printers:
            discovered_printers_model.removeDiscoveredPrinter(printer.address)

    @pyqtSlot()
    def refreshPrinters(self):
        self._resetPrinters()
        self._addPrinters()

    def _createMachine(self, device_id: str) -> None:
        global new_machine
        discovered_printers_model = self._cura_application.getDiscoveredPrintersModel()
        discovered_printers = discovered_printers_model.discoveredPrinters
        for printer in discovered_printers:
            if printer.getKey() == device_id:
                new_machine = CuraStackBuilder.createMachine(printer.name, "bcn3d" + printer.machineType[-3:].lower())

        if not new_machine:
            Logger.log("e", "Failed creating a new machine")
            return
        new_machine.setMetaDataEntry("is_network_machine", True)
        new_machine.setMetaDataEntry("serial_number", device_id)
        self._cura_application.getMachineManager().setActiveMachine(new_machine.getId())

    @classmethod
    def getInstance(cls) -> "PrintersManager":
        if not cls.__instance:
            cls.__instance = PrintersManager()
        return cls.__instance

    __instance = None