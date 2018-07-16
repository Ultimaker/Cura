from UM.Message import Message
from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")

class USBPrinterOutputDevicePatches():
    def __init__(self, output_device):
        self._output_device = output_device
        self._output_device.requestWrite = self.requestWrite

        self._output_device.setPriority(-1)

        controller = self._output_device._printers[0].getController()
        controller.can_control_manually = False

        self._not_supported_message = Message(i18n_catalog.i18nc("@info:status", "Printing via USB is not supported on BLACKBELT 3D printers. Please save the G-code to an SD-Card."))

    def requestWrite(self, nodes, file_name = None, filter_by_machine = False, file_handler = None, **kwargs):
        self._not_supported_message.show()
