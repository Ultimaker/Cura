# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import List

from cura.MachineAction import MachineAction
from cura.PrinterOutput.PrinterOutputDevice import PrinterOutputDevice

from UM.FlameProfiler import pyqtSlot

from UM.Application import Application
from UM.i18n import i18nCatalog
from UM.Logger import Logger
catalog = i18nCatalog("cura")


class BedLevelMachineAction(MachineAction):
    """A simple action to handle manual bed leveling procedure for printers that don't have it on the firmware.
    
    This is currently only used by the Ultimaker Original+
    """

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
        if not printer_output_devices:
            Logger.log("e", "Can't start bed levelling. The printer connection seems to have been lost.")
            return
        printer = printer_output_devices[0].activePrinter

        printer.homeBed()
        printer.moveHead(0, 0, 3)
        printer.homeHead()
        printer.homeBed()

    def _getPrinterOutputDevices(self) -> List[PrinterOutputDevice]:
        return [printer_output_device for printer_output_device in Application.getInstance().getOutputDeviceManager().getOutputDevices() if isinstance(printer_output_device, PrinterOutputDevice)]

    @pyqtSlot()
    def moveToNextLevelPosition(self):
        output_devices = self._getPrinterOutputDevices()
        if not output_devices: #No output devices. Can't move.
            Logger.log("e", "Can't move to the next position. The printer connection seems to have been lost.")
            return
        printer = output_devices[0].activePrinter

        if self._bed_level_position == 0:
            printer.moveHead(0, 0, 3)
            printer.homeHead()
            printer.moveHead(0, 0, 3)
            printer.moveHead(Application.getInstance().getGlobalContainerStack().getProperty("machine_width", "value") - 10, 0, 0)
            printer.moveHead(0, 0, -3)
            printer.homeBed()
            self._bed_level_position += 1
        elif self._bed_level_position == 1:
            printer.moveHead(0, 0, 3)
            printer.moveHead(-Application.getInstance().getGlobalContainerStack().getProperty("machine_width", "value" ) / 2, Application.getInstance().getGlobalContainerStack().getProperty("machine_depth", "value") - 10, 0)
            printer.moveHead(0, 0, -3)
            self._bed_level_position += 1
        elif self._bed_level_position == 2:
            printer.moveHead(0, 0, 3)
            printer.moveHead(-Application.getInstance().getGlobalContainerStack().getProperty("machine_width", "value") / 2 + 10, -(Application.getInstance().getGlobalContainerStack().getProperty("machine_depth", "value") + 10), 0)
            printer.moveHead(0, 0, -3)
            self._bed_level_position += 1
        elif self._bed_level_position >= 3:
            output_devices[0].sendCommand("M18") # Turn off all motors so the user can move the axes
            self.setFinished()