from PyQt6.QtCore import pyqtProperty, pyqtSlot

from cura.CuraApplication import CuraApplication
from UM.Application import Application
from UM.Message import Message
from UM.Logger import Logger


from .DataService import DataService
from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice


from UM.i18n import i18nCatalog

catalog = i18nCatalog("cura")


class Device(NetworkedPrinterOutputDevice):
    def __init__(self, name: str):
        id = "cloud"
        if name == "cloud_save":
            id = "cloud_save"

        super().__init__(device_id=id, address="address", properties=[])

        self._name = name
        message = catalog.i18nc("@action:button", "Send to printer") 
        if self._name == "cloud_save":
            message = catalog.i18nc("@action:button", "Send to cloud and print")
        self.setShortDescription(catalog.i18nc("@action:button Preceded by 'Ready to'.", message))
        self.setDescription(catalog.i18nc("@info:tooltip", message))
        self.setIconName("cloud")

        self._data_api_service = DataService.getInstance()

        self._gcode = []
        self._writing = False
        self._compressing_gcode = False
        self._progress_message = Message("Sending the gcode to the printer",
                                         title="Send to printer", dismissable=False, progress=-1)

    def requestWrite(self, nodes, file_name=None, limit_mimetypes=False, file_handler=None, **kwargs):
        self._progress_message.show()
        serial_number = Application.getInstance().getGlobalContainerStack().getMetaDataEntry("serial_number")
        if not serial_number:
            self._progress_message.hide()
            Message("The selected printer doesn't support this feature.", title="Can't send gcode to printer").show()
            return
        
        connectedPrinters = self._data_api_service.getConnectedPrinter()
        printer = None
        
        for p in connectedPrinters['data']:
            if p['serialNumber'] == serial_number:
                printer = p
                break
        
        if not printer:
            self._progress_message.hide()
            Message("The selected printer doesn't exist or you don't have permissions to print.",
                    title="Can't send gcode to printer").show()
            return
        if not printer["ready_to_print"]:
            self._progress_message.hide()
            Message("The selected printer isn't ready to print.", title="Can't send gcode to printer").show()
            return

        self.writeStarted.emit(self)
        active_build_plate = CuraApplication.getInstance().getMultiBuildPlateModel().activeBuildPlate
        self._gcode = getattr(Application.getInstance().getController().getScene(), "gcode_dict")[active_build_plate]
        gcode = self._joinGcode()
        file_name_with_extension = file_name + ".gcode"
        self._data_api_service.sendGcode(gcode, file_name_with_extension, printer['id'], self._name == "cloud_save")
        self.writeFinished.emit()
        self._progress_message.hide()

    def _joinGcode(self):
        gcode = ""
        for line in self._gcode:
            gcode += line
        return gcode

    @pyqtSlot(str, result=str)
    def getProperty(self, key: str) -> str:
        return ""

    @pyqtProperty(str, constant=True)
    def name(self) -> str:
        """Name of the printer (as returned from the ZeroConf properties)"""
        return self._name
