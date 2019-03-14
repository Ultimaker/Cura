# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from cura.PrinterOutput.PrinterOutputController import PrinterOutputController
from PyQt5.QtCore import QTimer
from UM.Version import Version

MYPY = False
if MYPY:
    from cura.PrinterOutput.PrintJobOutputModel import PrintJobOutputModel
    from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel


class LegacyUM3PrinterOutputController(PrinterOutputController):
    def __init__(self, output_device):
        super().__init__(output_device)
        self._preheat_bed_timer = QTimer()
        self._preheat_bed_timer.setSingleShot(True)
        self._preheat_bed_timer.timeout.connect(self._onPreheatBedTimerFinished)
        self._preheat_printer = None

        self.can_control_manually = False
        self.can_send_raw_gcode = False

        # Are we still waiting for a response about preheat?
        # We need this so we can already update buttons, so it feels more snappy.
        self._preheat_request_in_progress = False

    def isPreheatRequestInProgress(self):
        return self._preheat_request_in_progress

    def setJobState(self, job: "PrintJobOutputModel", state: str):
        data = "{\"target\": \"%s\"}" % state
        self._output_device.put("print_job/state", data, on_finished=None)

    def setTargetBedTemperature(self, printer: "PrinterOutputModel", temperature: float):
        data = str(temperature)
        self._output_device.put("printer/bed/temperature/target", data, on_finished = self._onPutBedTemperatureCompleted)

    def _onPutBedTemperatureCompleted(self, reply):
        if Version(self._preheat_printer.firmwareVersion) < Version("3.5.92"):
            # If it was handling a preheat, it isn't anymore.
            self._preheat_request_in_progress = False

    def _onPutPreheatBedCompleted(self, reply):
        self._preheat_request_in_progress = False

    def moveHead(self, printer: "PrinterOutputModel", x, y, z, speed):
        head_pos = printer._head_position
        new_x = head_pos.x + x
        new_y = head_pos.y + y
        new_z = head_pos.z + z
        data = "{\n\"x\":%s,\n\"y\":%s,\n\"z\":%s\n}" %(new_x, new_y, new_z)
        self._output_device.put("printer/heads/0/position", data, on_finished=None)

    def homeBed(self, printer):
        self._output_device.put("printer/heads/0/position/z", "0", on_finished=None)

    def _onPreheatBedTimerFinished(self):
        self.setTargetBedTemperature(self._preheat_printer, 0)
        self._preheat_printer.updateIsPreheating(False)
        self._preheat_request_in_progress = True

    def cancelPreheatBed(self, printer: "PrinterOutputModel"):
        self.preheatBed(printer, temperature=0, duration=0)
        self._preheat_bed_timer.stop()
        printer.updateIsPreheating(False)

    def preheatBed(self, printer: "PrinterOutputModel", temperature, duration):
        try:
            temperature = round(temperature)  # The API doesn't allow floating point.
            duration = round(duration)
        except ValueError:
            return  # Got invalid values, can't pre-heat.

        if duration > 0:
            data = """{"temperature": "%i", "timeout": "%i"}""" % (temperature, duration)
        else:
            data = """{"temperature": "%i"}""" % temperature

        # Real bed pre-heating support is implemented from 3.5.92 and up.

        if Version(printer.firmwareVersion) < Version("3.5.92"):
            # No firmware-side duration support then, so just set target bed temp and set a timer.
            self.setTargetBedTemperature(printer, temperature=temperature)
            self._preheat_bed_timer.setInterval(duration * 1000)
            self._preheat_bed_timer.start()
            self._preheat_printer = printer
            printer.updateIsPreheating(True)
            return

        self._output_device.put("printer/bed/pre_heat", data, on_finished = self._onPutPreheatBedCompleted)
        printer.updateIsPreheating(True)
        self._preheat_request_in_progress = True


