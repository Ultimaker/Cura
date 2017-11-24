# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from cura.PrinterOutput.PrinterOutputController import PrinterOutputController


class LegacyUM3PrinterOutputController(PrinterOutputController):
    def __init__(self, output_device):
        super().__init__(output_device)

    def setJobState(self, job: "PrintJobOutputModel", state: str):
        data = "{\"target\": \"%s\"}" % state
        self._output_device.put("print_job/state", data, onFinished=None)
