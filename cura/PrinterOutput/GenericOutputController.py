# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING, Set, Union, Optional

from cura.PrinterOutput.PrinterOutputController import PrinterOutputController
from PyQt5.QtCore import QTimer

if TYPE_CHECKING:
    from cura.PrinterOutput.PrintJobOutputModel import PrintJobOutputModel
    from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel
    from cura.PrinterOutput.PrinterOutputDevice import PrinterOutputDevice
    from cura.PrinterOutput.ExtruderOutputModel import ExtruderOutputModel


class GenericOutputController(PrinterOutputController):
    def __init__(self, output_device: "PrinterOutputDevice") -> None:
        super().__init__(output_device)

        self._preheat_bed_timer = QTimer()
        self._preheat_bed_timer.setSingleShot(True)
        self._preheat_bed_timer.timeout.connect(self._onPreheatBedTimerFinished)
        self._preheat_printer = None  # type: Optional[PrinterOutputModel]

        self._preheat_hotends_timer = QTimer()
        self._preheat_hotends_timer.setSingleShot(True)
        self._preheat_hotends_timer.timeout.connect(self._onPreheatHotendsTimerFinished)
        self._preheat_hotends = set()  # type: Set[ExtruderOutputModel]

        self._output_device.printersChanged.connect(self._onPrintersChanged)
        self._active_printer = None  # type: Optional[PrinterOutputModel]

    def _onPrintersChanged(self) -> None:
        if self._active_printer:
            self._active_printer.stateChanged.disconnect(self._onPrinterStateChanged)
            self._active_printer.targetBedTemperatureChanged.disconnect(self._onTargetBedTemperatureChanged)
            for extruder in self._active_printer.extruders:
                extruder.targetHotendTemperatureChanged.disconnect(self._onTargetHotendTemperatureChanged)

        self._active_printer = self._output_device.activePrinter
        if self._active_printer:
            self._active_printer.stateChanged.connect(self._onPrinterStateChanged)
            self._active_printer.targetBedTemperatureChanged.connect(self._onTargetBedTemperatureChanged)
            for extruder in self._active_printer.extruders:
                extruder.targetHotendTemperatureChanged.connect(self._onTargetHotendTemperatureChanged)

    def _onPrinterStateChanged(self) -> None:
        if self._active_printer and self._active_printer.state != "idle":
            if self._preheat_bed_timer.isActive():
                self._preheat_bed_timer.stop()
                if self._preheat_printer:
                    self._preheat_printer.updateIsPreheating(False)
            if self._preheat_hotends_timer.isActive():
                self._preheat_hotends_timer.stop()
                for extruder in self._preheat_hotends:
                    extruder.updateIsPreheating(False)
                self._preheat_hotends = set()  # type: Set[ExtruderOutputModel]

    def moveHead(self, printer: "PrinterOutputModel", x, y, z, speed) -> None:
        self._output_device.sendCommand("G91")
        self._output_device.sendCommand("G0 X%s Y%s Z%s F%s" % (x, y, z, speed))
        self._output_device.sendCommand("G90")

    def homeHead(self, printer: "PrinterOutputModel") -> None:
        self._output_device.sendCommand("G28 X Y")

    def homeBed(self, printer: "PrinterOutputModel") -> None:
        self._output_device.sendCommand("G28 Z")

    def sendRawCommand(self, printer: "PrinterOutputModel", command: str) -> None:
        self._output_device.sendCommand(command.upper()) #Most printers only understand uppercase g-code commands.

    def setJobState(self, job: "PrintJobOutputModel", state: str) -> None:
        if state == "pause":
            self._output_device.pausePrint()
            job.updateState("paused")
        elif state == "print":
            self._output_device.resumePrint()
            job.updateState("printing")
        elif state == "abort":
            self._output_device.cancelPrint()
            pass

    def setTargetBedTemperature(self, printer: "PrinterOutputModel", temperature: float) -> None:
        self._output_device.sendCommand("M140 S%s" % round(temperature)) # The API doesn't allow floating point.

    def _onTargetBedTemperatureChanged(self) -> None:
        if self._preheat_bed_timer.isActive() and self._preheat_printer and self._preheat_printer.targetBedTemperature == 0:
            self._preheat_bed_timer.stop()
            self._preheat_printer.updateIsPreheating(False)

    def preheatBed(self, printer: "PrinterOutputModel", temperature, duration) -> None:
        try:
            temperature = round(temperature)  # The API doesn't allow floating point.
            duration = round(duration)
        except ValueError:
            return  # Got invalid values, can't pre-heat.

        self.setTargetBedTemperature(printer, temperature = temperature)
        self._preheat_bed_timer.setInterval(duration * 1000)
        self._preheat_bed_timer.start()
        self._preheat_printer = printer
        printer.updateIsPreheating(True)

    def cancelPreheatBed(self, printer: "PrinterOutputModel") -> None:
        self.setTargetBedTemperature(printer, temperature = 0)
        self._preheat_bed_timer.stop()
        printer.updateIsPreheating(False)

    def _onPreheatBedTimerFinished(self) -> None:
        if not self._preheat_printer:
            return
        self.setTargetBedTemperature(self._preheat_printer, 0)
        self._preheat_printer.updateIsPreheating(False)

    def setTargetHotendTemperature(self, printer: "PrinterOutputModel", position: int, temperature: Union[int, float]) -> None:
        self._output_device.sendCommand("M104 S%s T%s" % (temperature, position))

    def _onTargetHotendTemperatureChanged(self) -> None:
        if not self._preheat_hotends_timer.isActive():
            return
        if not self._active_printer:
            return

        for extruder in self._active_printer.extruders:
            if extruder in self._preheat_hotends and extruder.targetHotendTemperature == 0:
                extruder.updateIsPreheating(False)
                self._preheat_hotends.remove(extruder)
        if not self._preheat_hotends:
            self._preheat_hotends_timer.stop()

    def preheatHotend(self, extruder: "ExtruderOutputModel", temperature, duration) -> None:
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
        self._preheat_hotends_timer.setInterval(duration * 1000)
        self._preheat_hotends_timer.start()
        self._preheat_hotends.add(extruder)
        extruder.updateIsPreheating(True)

    def cancelPreheatHotend(self, extruder: "ExtruderOutputModel") -> None:
        self.setTargetHotendTemperature(extruder.getPrinter(), extruder.getPosition(), temperature=0)
        if extruder in self._preheat_hotends:
            extruder.updateIsPreheating(False)
            self._preheat_hotends.remove(extruder)
        if not self._preheat_hotends and self._preheat_hotends_timer.isActive():
            self._preheat_hotends_timer.stop()

    def _onPreheatHotendsTimerFinished(self) -> None:
        for extruder in self._preheat_hotends:
            self.setTargetHotendTemperature(extruder.getPrinter(), extruder.getPosition(), 0)
        self._preheat_hotends = set() #type: Set[ExtruderOutputModel]

    # Cancel any ongoing preheating timers, without setting back the temperature to 0
    # This can be used eg at the start of a print
    def stopPreheatTimers(self) -> None:
        if self._preheat_hotends_timer.isActive():
            for extruder in self._preheat_hotends:
                extruder.updateIsPreheating(False)
            self._preheat_hotends = set() #type: Set[ExtruderOutputModel]

            self._preheat_hotends_timer.stop()

        if self._preheat_bed_timer.isActive():
            if self._preheat_printer:
                self._preheat_printer.updateIsPreheating(False)
            self._preheat_bed_timer.stop()
