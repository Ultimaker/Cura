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

 # Function to set the state checked inside the qml of the plugin
    @pyqtSlot(result = str)
    def getPrintMode(self):
        self._global_container_stack = self._application.getGlobalContainerStack()
        print_mode = self._global_container_stack.getProperty("print_mode", "value")
        return print_mode

    @pyqtSlot(str)
    def setPrintMode(self, print_mode: str):
        # setPrintModeToLoad does not exists in CuraApplication, we need either to modifify it as a plugin to override functions and params, or save the parameter in our plugins"""
        #self._application.setPrintModeToLoad(print_mode)
        self._global_container_stack = self._application.getGlobalContainerStack()
        #left_extruder = self._global_container_stack.extruderList[0]
        #right_extruder = self._global_container_stack.extruderList[1]
        try:
            '''Exception on self._onEnabledChangedLeft/_onEnabledChangedRight Due it does not exits
                in class, perhaps this should be in other class but why do we disable it?
            '''
            #left_extruder.enabledChanged.disconnect(self._onEnabledChangedLeft)
            #right_extruder.enabledChanged.disconnect(self._onEnabledChangedRight)
            self._application.getMachineManager().setExtruderEnabled(0, False)
            self._application.getMachineManager().setExtruderEnabled(1, False)
        except Exception as e:
            Logger.error ("error setting extruders: ".format(e))
            pass
        if print_mode == "singleT0":
            self._global_container_stack.setProperty("print_mode", "value", "singleT0")

            # Now we select all the nodes and set the printmode to them to avoid different nodes on differents printmodes

            CuraApplication.selectAll(CuraApplication.getInstance())
            for node in Selection.getAllSelectedObjects():
                node.setSetting("print_mode", "singleTO")

        elif print_mode == "singleT1":
            self._global_container_stack.setProperty("print_mode", "value", "singleT1")
            CuraApplication.selectAll(CuraApplication.getInstance())
            for node in Selection.getAllSelectedObjects():
                node.setSetting("print_mode", "singleT1")

        elif print_mode == "dual":
            self._global_container_stack.setProperty("print_mode", "value", "dual")
            CuraApplication.selectAll(CuraApplication.getInstance())
            for node in Selection.getAllSelectedObjects():
                node.setSetting("print_mode", "dual")

        elif print_mode == "mirror":
            self._global_container_stack.setProperty("print_mode", "value", "mirror")
            CuraApplication.selectAll(CuraApplication.getInstance())
            for node in Selection.getAllSelectedObjects():
                node.setSetting("print_mode", "mirror")

        elif print_mode == "duplication":
            self._global_container_stack.setProperty("print_mode", "value", "duplication")
            CuraApplication.selectAll(CuraApplication.getInstance())
            for node in Selection.getAllSelectedObjects():
                node.setSetting("print_mode", "duplication")
