

MYPY = False
if MYPY:
    from cura.PrinterOutput.PrintJobOutputModel import PrintJobOutputModel
    from cura.PrinterOutput.ExtruderOuputModel import ExtruderOuputModel
    from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel

class PrinterOutputController:
    def __init__(self):
        pass

    def setTargetHotendTemperature(self, printer: "PrinterOutputModel", extruder: "ExtruderOuputModel", temperature: int):
        # TODO: implement
        pass

    def setTargetBedTemperature(self, printer: "PrinterOutputModel", temperature: int):
        pass

    def setJobState(self, job: "PrintJobOutputModel", state: str):
        pass