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

    def setTargetBedTemperature(self, printer: "PrinterOutputModel", temperature: int):
        self._output_device.sendCommand("M140 S%s" % temperature)

    def _onPreheatBedTimerFinished(self):
        self.setTargetBedTemperature(self._preheat_printer, 0)
        self._preheat_printer.updateIsPreheating(False)