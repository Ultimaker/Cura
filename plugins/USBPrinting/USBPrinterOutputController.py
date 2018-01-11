# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from cura.PrinterOutput.PrinterOutputController import PrinterOutputController
from PyQt5.QtCore import QTimer

MYPY = False
if MYPY:
    from cura.PrinterOutput.PrintJobOutputModel import PrintJobOutputModel
    from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel


class USBPrinterOuptutController(PrinterOutputController):
    def __init__(self, output_device):
        super().__init__(output_device)

        self._preheat_bed_timer = QTimer()
        self._preheat_bed_timer.setSingleShot(True)
        self._preheat_bed_timer.timeout.connect(self._onPreheatBedTimerFinished)
        self._preheat_printer = None

        self._preheat_extruders_timer = QTimer()
        self._preheat_extruders_timer.setSingleShot(True)
        self._preheat_extruders_timer.timeout.connect(self._onPreheatHotendsTimerFinished)
        self._preheat_extruders = set()

    def moveHead(self, printer: "PrinterOutputModel", x, y, z, speed):
        self._output_device.sendCommand("G91")
        self._output_device.sendCommand("G0 X%s Y%s Z%s F%s" % (x, y, z, speed))
        self._output_device.sendCommand("G90")

    def homeHead(self, printer):
        self._output_device.sendCommand("G28 X")
        self._output_device.sendCommand("G28 Y")

    def homeBed(self, printer):
        self._output_device.sendCommand("G28 Z")

    def setJobState(self, job: "PrintJobOutputModel", state: str):
        if state == "pause":
            self._output_device.pausePrint()
            job.updateState("paused")
        elif state == "print":
            self._output_device.resumePrint()
            job.updateState("printing")
        elif state == "abort":
            self._output_device.cancelPrint()
            pass

    def setTargetBedTemperature(self, printer: "PrinterOutputModel", temperature: int):
        self._output_device.sendCommand("M140 S%s" % temperature)

    def preheatBed(self, printer: "PrinterOutputModel", temperature, duration):
        try:
            temperature = round(temperature)  # The API doesn't allow floating point.
            duration = round(duration)
        except ValueError:
            return  # Got invalid values, can't pre-heat.

        self.setTargetBedTemperature(printer, temperature=temperature)
        self._preheat_bed_timer.setInterval(duration * 1000)
        self._preheat_bed_timer.start()
        self._preheat_printer = printer
        printer.updateIsPreheating(True)

    def cancelPreheatBed(self, printer: "PrinterOutputModel"):
        self.preheatBed(printer, temperature=0, duration=0)
        self._preheat_bed_timer.stop()
        printer.updateIsPreheating(False)

    def _onPreheatBedTimerFinished(self):
        self.setTargetBedTemperature(self._preheat_printer, 0)
        self._preheat_printer.updateIsPreheating(False)

    def setTargetHotendTemperature(self, printer: "PrinterOutputModel", position: int, temperature: int):
        self._output_device.sendCommand("M104 S%s T%s" % (temperature, position))

    def _onPreheatHotendsTimerFinished(self):
        for extruder in self._preheat_extruders:
            self.setTargetHotendTemperature(extruder.getPrinter(), extruder.getPosition(), 0)
        self._preheat_extruders = set()
        self._preheat_printer.updateIsPreheating(False)

    def cancelPreheatHotend(self, extruder: "ExtruderOutputModel"):
        self.preheatHotend(extruder, temperature=0, duration=0)
        self._preheat_extruders_timer.stop()
        try:
            self._preheat_extruders.remove(extruder)
        except KeyError:
            pass
        extruder.updateIsPreheating(False)

    def preheatHotend(self, extruder: "ExtruderOutputModel", temperature, duration):
        position = extruder.getPosition()
        number_of_extruders = len(extruder.getPrinter().extruders)
        if position >= number_of_extruders:
            return  # Got invalid extruder nr, can't pre-heat.

        try:
            temperature = round(temperature)  # The API doesn't allow floating point.
            duration = round(duration)
        except ValueError:
            return  # Got invalid values, can't pre-heat.

        self.setTargetHotendTemperature(extruder.getPrinter(), position, temperature=temperature)
        self._preheat_extruders_timer.setInterval(duration * 1000)
        self._preheat_extruders_timer.start()
        self._preheat_extruders.add(extruder)
        extruder.updateIsPreheating(True)