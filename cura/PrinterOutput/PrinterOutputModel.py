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
    isPreheatingChanged = pyqtSignal()
    stateChanged = pyqtSignal()
    activePrintJobChanged = pyqtSignal()
    nameChanged = pyqtSignal()
    headPositionChanged = pyqtSignal()
    keyChanged = pyqtSignal()
    typeChanged = pyqtSignal()
    cameraChanged = pyqtSignal()

    def __init__(self, output_controller: "PrinterOutputController", number_of_extruders: int = 1, parent=None, firmware_version = ""):
        super().__init__(parent)
        self._bed_temperature = -1  # Use -1 for no heated bed.
        self._target_bed_temperature = 0
        self._name = ""
        self._key = ""  # Unique identifier
        self._controller = output_controller
        self._extruders = [ExtruderOutputModel(printer=self) for i in range(number_of_extruders)]
        self._head_position = Vector(0, 0, 0)
        self._active_print_job = None  # type: Optional[PrintJobOutputModel]
        self._firmware_version = firmware_version
        self._printer_state = "unknown"
        self._is_preheating = False
        self._type = ""

        self._camera = None

    @pyqtProperty(str, constant = True)
    def firmwareVersion(self):
        return self._firmware_version

    def setCamera(self, camera):
        if self._camera is not camera:
            self._camera = camera
            self.cameraChanged.emit()

    def updateIsPreheating(self, pre_heating):
        if self._is_preheating != pre_heating:
            self._is_preheating = pre_heating
            self.isPreheatingChanged.emit()

    @pyqtProperty(bool, notify=isPreheatingChanged)
    def isPreheating(self):
        return self._is_preheating

    @pyqtProperty(QObject, notify=cameraChanged)
    def camera(self):
        return self._camera

    @pyqtProperty(str, notify = typeChanged)
    def type(self):
        return self._type

    def updateType(self, type):
        if self._type != type:
            self._type = type
            self.typeChanged.emit()

    @pyqtProperty(str, notify=keyChanged)
    def key(self):
        return self._key

    def updateKey(self, key: str):
        if self._key != key:
            self._key = key
            self.keyChanged.emit()

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
        self.updateHeadPosition(x, y, z)
        self._controller.setHeadPosition(self, x, y, z, speed)

    @pyqtProperty("long")
    @pyqtProperty("long", "long")
    def setHeadX(self, x, speed = 3000):
        self.updateHeadPosition(x, self._head_position.y, self._head_position.z)
        self._controller.setHeadPosition(self, x, self._head_position.y, self._head_position.z, speed)

    @pyqtProperty("long")
    @pyqtProperty("long", "long")
    def setHeadY(self, y, speed = 3000):
        self.updateHeadPosition(self._head_position.x, y, self._head_position.z)
        self._controller.setHeadPosition(self, self._head_position.x, y, self._head_position.z, speed)

    @pyqtProperty("long")
    @pyqtProperty("long", "long")
    def setHeadZ(self, z, speed = 3000):
        self.updateHeadPosition(self._head_position.x, self._head_position.y, z)
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
            old_print_job = self._active_print_job

            if print_job is not None:
                print_job.updateAssignedPrinter(self)
            self._active_print_job = print_job

            if old_print_job is not None:
                old_print_job.updateAssignedPrinter(None)
            self.activePrintJobChanged.emit()

    def updateState(self, printer_state):
        if self._printer_state != printer_state:
            self._printer_state = printer_state
            self.stateChanged.emit()

    @pyqtProperty(QObject, notify = activePrintJobChanged)
    def activePrintJob(self):
        return self._active_print_job

    @pyqtProperty(str, notify=stateChanged)
    def state(self):
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
        if self._controller:
            return self._controller.can_pre_heat_bed
        return False

    # Does the printer support pause at all
    @pyqtProperty(bool, constant=True)
    def canPause(self):
        if self._controller:
            return self._controller.can_pause
        return False

    # Does the printer support abort at all
    @pyqtProperty(bool, constant=True)
    def canAbort(self):
        if self._controller:
            return self._controller.can_abort
        return False

    # Does the printer support manual control at all
    @pyqtProperty(bool, constant=True)
    def canControlManually(self):
        if self._controller:
            return self._controller.can_control_manually
        return False
