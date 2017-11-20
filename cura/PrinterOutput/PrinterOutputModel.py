# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtSignal, pyqtProperty, QObject, QVariant, pyqtSlot
from UM.Logger import Logger
from typing import Optional, List
from UM.Math.Vector import Vector
from cura.PrinterOutput.ExtruderOuputModel import ExtruderOutputModel

MYPY = False
if MYPY:
    from cura.PrinterOutput.PrintJobOutputModel import PrintJobOutputModel
    from cura.PrinterOutput.PrinterOutputController import PrinterOutputController


class PrinterOutputModel(QObject):
    bedTemperatureChanged = pyqtSignal()
    targetBedTemperatureChanged = pyqtSignal()
    printerStateChanged = pyqtSignal()
    activePrintJobChanged = pyqtSignal()
    nameChanged = pyqtSignal()
    headPositionChanged = pyqtSignal()

    def __init__(self, output_controller: "PrinterOutputController", number_of_extruders: int = 1, parent=None):
        super().__init__(parent)
        self._bed_temperature = 0
        self._target_bed_temperature = 0
        self._name = ""
        self._controller = output_controller
        self._extruders = [ExtruderOutputModel(printer=self)] * number_of_extruders

        self._head_position = Vector(0, 0, 0)
        self._active_print_job = None  # type: Optional[PrintJobOutputModel]

        self._printer_state = "unknown"

        # Features of the printer;
        self._can_pause = True
        self._can_abort = True
        self._can_pre_heat_bed = True
        self._can_control_manually = True

    @pyqtSlot()
    def homeHead(self):
        self._controller.homeHead(self)

    @pyqtSlot()
    def homeBed(self):
        self._controller.homeBed(self)

    @pyqtProperty("QVariantList", constant = True)
    def extruders(self):
        return self._extruders

    @pyqtProperty(QVariant, notify = headPositionChanged)
    def headPosition(self):
        return {"x": self._head_position.x, "y": self._head_position.y, "z": self.head_position_z}

    def updateHeadPosition(self, x, y, z):
        if self._head_position.x != x or self._head_position.y != y or self._head_position.z != z:
            self._head_position = Vector(x, y, z)
            self.headPositionChanged.emit()

    @pyqtProperty("long", "long", "long")
    @pyqtProperty("long", "long", "long", "long")
    def setHeadPosition(self, x, y, z, speed = 3000):
        self._controller.setHeadPosition(self, x, y, z, speed)

    @pyqtProperty("long")
    @pyqtProperty("long", "long")
    def setHeadX(self, x, speed = 3000):
        self._controller.setHeadPosition(self, x, self._head_position.y, self._head_position.z, speed)

    @pyqtProperty("long")
    @pyqtProperty("long", "long")
    def setHeadY(self, y, speed = 3000):
        self._controller.setHeadPosition(self, self._head_position.x, y, self._head_position.z, speed)

    @pyqtProperty("long")
    @pyqtProperty("long", "long")
    def setHeadY(self, z, speed = 3000):
        self._controller.setHeadPosition(self, self._head_position.x, self._head_position.y, z, speed)

    @pyqtSlot("long", "long", "long")
    @pyqtSlot("long", "long", "long", "long")
    def moveHead(self, x = 0, y = 0, z = 0, speed = 3000):
        self._controller.moveHead(self, x, y, z, speed)

    ##  Pre-heats the heated bed of the printer.
    #
    #   \param temperature The temperature to heat the bed to, in degrees
    #   Celsius.
    #   \param duration How long the bed should stay warm, in seconds.
    @pyqtSlot(float, float)
    def preheatBed(self, temperature, duration):
        self._controller.preheatBed(self, temperature, duration)

    @pyqtSlot()
    def cancelPreheatBed(self):
        self._controller.cancelPreheatBed(self)

    def getController(self):
        return self._controller

    @pyqtProperty(str, notify=nameChanged)
    def name(self):
        return self._name

    def setName(self, name):
        self._setName(name)
        self.updateName(name)

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
        self._controller.setTargetBedTemperature(self, temperature)
        self.updateTargetBedTemperature(temperature)

    def updateActivePrintJob(self, print_job):
        if self._active_print_job != print_job:
            self._active_print_job = print_job
            self.activePrintJobChanged.emit()

    def updatePrinterState(self, printer_state):
        if self._printer_state != printer_state:
            self._printer_state = printer_state
            self.printerStateChanged.emit()

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
