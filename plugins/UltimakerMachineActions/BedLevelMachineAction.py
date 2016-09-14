from cura.MachineAction import MachineAction
from cura.PrinterOutputDevice import PrinterOutputDevice

from PyQt5.QtCore import pyqtSlot

from UM.Application import Application
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


class BedLevelMachineAction(MachineAction):
    def __init__(self):
        super().__init__("BedLevel", catalog.i18nc("@action", "Level build plate"))
        self._qml_url = "BedLevelMachineAction.qml"
        self._bed_level_position = 0

    def _execute(self):
        pass

    def _reset(self):
        self._bed_level_position = 0
        pass

    @pyqtSlot()
    def startBedLeveling(self):
        self._bed_level_position = 0
        printer_output_devices = self._getPrinterOutputDevices()
        if printer_output_devices:
            printer_output_devices[0].homeBed()
            printer_output_devices[0].moveHead(0, 0, 3)
            printer_output_devices[0].homeHead()

    def _getPrinterOutputDevices(self):
        return [printer_output_device for printer_output_device in Application.getInstance().getOutputDeviceManager().getOutputDevices() if isinstance(printer_output_device, PrinterOutputDevice)]

    @pyqtSlot()
    def moveToNextLevelPosition(self):
        output_devices = self._getPrinterOutputDevices()
        if output_devices:  # We found at least one output device
            output_device = output_devices[0]

            if self._bed_level_position == 0:
                output_device.moveHead(0, 0, 3)
                output_device.homeHead()
                output_device.moveHead(0, 0, 3)
                output_device.moveHead(Application.getInstance().getGlobalContainerStack().getProperty("machine_width", "value") - 10, 0, 0)
                output_device.moveHead(0, 0, -3)
                self._bed_level_position += 1
            elif self._bed_level_position == 1:
                output_device.moveHead(0, 0, 3)
                output_device.moveHead(-Application.getInstance().getGlobalContainerStack().getProperty("machine_width", "value" ) / 2, Application.getInstance().getGlobalContainerStack().getProperty("machine_depth", "value") - 10, 0)
                output_device.moveHead(0, 0, -3)
                self._bed_level_position += 1
            elif self._bed_level_position == 2:
                output_device.moveHead(0, 0, 3)
                output_device.moveHead(-Application.getInstance().getGlobalContainerStack().getProperty("machine_width", "value") / 2 + 10, -(Application.getInstance().getGlobalContainerStack().getProperty("machine_depth", "value") + 10), 0)
                output_device.moveHead(0, 0, -3)
                self._bed_level_position += 1
            elif self._bed_level_position >= 3:
                output_device.sendCommand("M18") # Turn off all motors so the user can move the axes
                self.setFinished()