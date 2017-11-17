# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtSignal, pyqtProperty, QObject, QVariant, pyqtSlot
from UM.Logger import Logger
from typing import Optional, List

MYPY = False
if MYPY:
    from cura.PrinterOutput.PrintJobModel import PrintJobModel
    from cura.PrinterOutput.ExtruderModel import ExtruderModel


class PrinterModel(QObject):
    bedTemperatureChanged = pyqtSignal()
    targetBedTemperatureChanged = pyqtSignal()
    printerStateChanged = pyqtSignal()
    activePrintJobChanged = pyqtSignal()
    nameChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bed_temperature = 0
        self._target_bed_temperature = 0
        self._name = ""

        self._extruders = []  # type: List[ExtruderModel]

        self._active_print_job = None  # type: Optional[PrintJobModel]

        # Features of the printer;
        self._can_pause = True
        self._can_abort = True
        self._can_pre_heat_bed = True
        self._can_control_manually = True

    @pyqtProperty(str, notify=nameChanged)
    def name(self):
        return self._name

    def setName(self, name):
        self._setName(name)
        self.updateName(name)

    def _setName(self, name):
        Logger.log("w", "_setTargetBedTemperature is not implemented by this model")

    def updateName(self, name):
        if self._name != name:
            self._name = name
            self.nameChanged.emit()

    ##  Update the bed temperature. This only changes it locally.
    def updateBedTemperature(self, temperature):
        if self._bed_temperature != temperature:
            self._bed_temperature = temperature
            self.bedTemperatureChanged.emit()

    def updateTargetBedTemperature(self, temperature):
        if self._target_bed_temperature != temperature:
            self._target_bed_temperature = temperature
            self.targetBedTemperatureChanged.emit()

    ##  Set the target bed temperature. This ensures that it's actually sent to the remote.
    @pyqtSlot(int)
    def setTargetBedTemperature(self, temperature):
        self._setTargetBedTemperature(temperature)
        self.updateTargetBedTemperature(temperature)

    ##  Protected setter for the bed temperature of the connected printer (if any).
    #   /parameter temperature Temperature bed needs to go to (in deg celsius)
    #   /sa setTargetBedTemperature
    def _setTargetBedTemperature(self, temperature):
        Logger.log("w", "_setTargetBedTemperature is not implemented by this model")

    def updateActivePrintJob(self, print_job):
        if self._active_print_job != print_job:
            self._active_print_job = print_job
            self.activePrintJobChanged.emit()

    @pyqtProperty(QObject, notify = activePrintJobChanged)
    def activePrintJob(self):
        return self._active_print_job

    @pyqtProperty(str, notify=printerStateChanged)
    def printerState(self):
        return self._printer_state

    @pyqtProperty(int, notify = bedTemperatureChanged)
    def bedTemperature(self):
        return self._bed_temperature

    @pyqtProperty(int, notify=targetBedTemperatureChanged)
    def targetBedTemperature(self):
        return self._target_bed_temperature

    # Does the printer support pre-heating the bed at all
    @pyqtProperty(bool, constant=True)
    def canPreHeatBed(self):
        return self._can_pre_heat_bed

    # Does the printer support pause at all
    @pyqtProperty(bool, constant=True)
    def canPause(self):
        return self._can_pause

    # Does the printer support abort at all
    @pyqtProperty(bool, constant=True)
    def canAbort(self):
        return self._can_abort

    # Does the printer support manual control at all
    @pyqtProperty(bool, constant=True)
    def canControlManually(self):
        return self._can_control_manually
