# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from cura.PrinterOutput.PrinterOutputController import PrinterOutputController

MYPY = False
if MYPY:
    from cura.PrinterOutput.PrintJobOutputModel import PrintJobOutputModel
    from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel


class LegacyUM3PrinterOutputController(PrinterOutputController):
    def __init__(self, output_device):
        super().__init__(output_device)

    def setJobState(self, job: "PrintJobOutputModel", state: str):
        data = "{\"target\": \"%s\"}" % state
        self._output_device.put("print_job/state", data, onFinished=None)

    def moveHead(self, printer: "PrinterOutputModel", x, y, z, speed):
        head_pos = printer._head_position
        new_x = head_pos.x + x
        new_y = head_pos.y + y
        new_z = head_pos.z + z
        data = "{\n\"x\":%s,\n\"y\":%s,\n\"z\":%s\n}" %(new_x, new_y, new_z)
        self._output_device.put("printer/heads/0/position", data, onFinished=None)

    def homeBed(self, printer):
        self._output_device.put("printer/heads/0/position/z", "0", onFinished=None)
