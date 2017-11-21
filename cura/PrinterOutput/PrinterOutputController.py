

MYPY = False
if MYPY:
    from cura.PrinterOutput.PrintJobOutputModel import PrintJobOutputModel
    from cura.PrinterOutput.ExtruderOuputModel import ExtruderOuputModel
    from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel


class PrinterOutputController:
    def __init__(self):
        self.can_pause = True
        self.can_abort = True
        self.can_pre_heat_bed = True
        self.can_control_manually = True

    def setTargetHotendTemperature(self, printer: "PrinterOutputModel", extruder: "ExtruderOuputModel", temperature: int):
        # TODO: implement
        pass

    def setTargetBedTemperature(self, printer: "PrinterOutputModel", temperature: int):
        pass

    def setJobState(self, job: "PrintJobOutputModel", state: str):
        pass

    def cancelPreheatBed(self, printer: "PrinterOutputModel"):
        pass

    def preheatBed(self, printer: "PrinterOutputModel", temperature, duration):
        pass

    def setHeadPosition(self, printer: "PrinterOutputModel", x, y, z, speed):
        pass

    def moveHead(self, printer: "PrinterOutputModel", x, y, z, speed):
        pass

    def homeBed(self, printer):
        pass

    def homeHead(self, printer):
        pass