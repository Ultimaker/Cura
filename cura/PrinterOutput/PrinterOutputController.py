# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Logger import Logger
from UM.Signal import Signal

MYPY = False
if MYPY:
    from .Models.PrintJobOutputModel import PrintJobOutputModel
    from .Models.ExtruderOutputModel import ExtruderOutputModel
    from .Models.PrinterOutputModel import PrinterOutputModel
    from .PrinterOutputDevice import PrinterOutputDevice


class PrinterOutputController:
    def __init__(self, output_device: "PrinterOutputDevice") -> None:
        self.can_pause = True
        self.can_abort = True
        self.can_pre_heat_bed = True
        self.can_pre_heat_hotends = True
        self.can_send_raw_gcode = True
        self.can_control_manually = True
        self.can_update_firmware = False
        self._output_device = output_device

    def setTargetHotendTemperature(self, printer: "PrinterOutputModel", position: int, temperature: float) -> None:
        Logger.log("w", "Set target hotend temperature not implemented in controller")

    def setTargetBedTemperature(self, printer: "PrinterOutputModel", temperature: float) -> None:
        Logger.log("w", "Set target bed temperature not implemented in controller")

    def setJobState(self, job: "PrintJobOutputModel", state: str) -> None:
        Logger.log("w", "Set job state not implemented in controller")

    def cancelPreheatBed(self, printer: "PrinterOutputModel") -> None:
        Logger.log("w", "Cancel preheat bed not implemented in controller")

    def preheatBed(self, printer: "PrinterOutputModel", temperature, duration) -> None:
        Logger.log("w", "Preheat bed not implemented in controller")

    def cancelPreheatHotend(self, extruder: "ExtruderOutputModel") -> None:
        Logger.log("w", "Cancel preheat hotend not implemented in controller")

    def preheatHotend(self, extruder: "ExtruderOutputModel", temperature, duration) -> None:
        Logger.log("w", "Preheat hotend not implemented in controller")

    def setHeadPosition(self, printer: "PrinterOutputModel", x, y, z, speed) -> None:
        Logger.log("w", "Set head position not implemented in controller")

    def moveHead(self, printer: "PrinterOutputModel", x, y, z, speed) -> None:
        Logger.log("w", "Move head not implemented in controller")

    def homeBed(self, printer: "PrinterOutputModel") -> None:
        Logger.log("w", "Home bed not implemented in controller")

    def homeHead(self, printer: "PrinterOutputModel") -> None:
        Logger.log("w", "Home head not implemented in controller")

    def sendRawCommand(self, printer: "PrinterOutputModel", command: str) -> None:
        Logger.log("w", "Custom command not implemented in controller")

    canUpdateFirmwareChanged = Signal()
    def setCanUpdateFirmware(self, can_update_firmware: bool) -> None:
        if can_update_firmware != self.can_update_firmware:
            self.can_update_firmware = can_update_firmware
            self.canUpdateFirmwareChanged.emit()