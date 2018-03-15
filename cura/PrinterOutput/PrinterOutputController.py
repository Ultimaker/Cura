# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Logger import Logger

MYPY = False
if MYPY:
    from cura.PrinterOutput.PrintJobOutputModel import PrintJobOutputModel
    from cura.PrinterOutput.ExtruderOutputModel import ExtruderOutputModel
    from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel


class PrinterOutputController:
    def __init__(self, output_device):
        self.can_pause = True
        self.can_abort = True
        self.can_pre_heat_bed = True
        self.can_pre_heat_hotends = True
        self.can_send_raw_gcode = True
        self.can_control_manually = True
        self._output_device = output_device

    def setTargetHotendTemperature(self, printer: "PrinterOutputModel", extruder: "ExtruderOutputModel", temperature: int):
        Logger.log("w", "Set target hotend temperature not implemented in controller")

    def setTargetBedTemperature(self, printer: "PrinterOutputModel", temperature: int):
        Logger.log("w", "Set target bed temperature not implemented in controller")

    def setJobState(self, job: "PrintJobOutputModel", state: str):
        Logger.log("w", "Set job state not implemented in controller")

    def cancelPreheatBed(self, printer: "PrinterOutputModel"):
        Logger.log("w", "Cancel preheat bed not implemented in controller")

    def preheatBed(self, printer: "PrinterOutputModel", temperature, duration):
        Logger.log("w", "Preheat bed not implemented in controller")

    def cancelPreheatHotend(self, extruder: "ExtruderOutputModel"):
        Logger.log("w", "Cancel preheat hotend not implemented in controller")

    def preheatHotend(self, extruder: "ExtruderOutputModel", temperature, duration):
        Logger.log("w", "Preheat hotend not implemented in controller")

    def setHeadPosition(self, printer: "PrinterOutputModel", x, y, z, speed):
        Logger.log("w", "Set head position not implemented in controller")

    def moveHead(self, printer: "PrinterOutputModel", x, y, z, speed):
        Logger.log("w", "Move head not implemented in controller")

    def homeBed(self, printer: "PrinterOutputModel"):
        Logger.log("w", "Home bed not implemented in controller")

    def homeHead(self, printer: "PrinterOutputModel"):
        Logger.log("w", "Home head not implemented in controller")

    def sendRawCommand(self, printer: "PrinterOutputModel", command: str):
        Logger.log("w", "Custom command not implemented in controller")
