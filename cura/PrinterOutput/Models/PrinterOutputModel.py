# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtSignal, pyqtProperty, QObject, QVariant, pyqtSlot, QUrl
from typing import List, Dict, Optional
from UM.Math.Vector import Vector
from cura.PrinterOutput.Models.PrinterConfigurationModel import PrinterConfigurationModel
from cura.PrinterOutput.Models.ExtruderOutputModel import ExtruderOutputModel

MYPY = False
if MYPY:
    from cura.PrinterOutput.Models.PrintJobOutputModel import PrintJobOutputModel
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
    buildplateChanged = pyqtSignal()
    cameraUrlChanged = pyqtSignal()
    configurationChanged = pyqtSignal()
    canUpdateFirmwareChanged = pyqtSignal()

    def __init__(self, output_controller: "PrinterOutputController", number_of_extruders: int = 1, parent=None, firmware_version = "") -> None:
        super().__init__(parent)
        self._bed_temperature = -1  # type: float  # Use -1 for no heated bed.
        self._target_bed_temperature = 0 # type: float
        self._name = ""
        self._key = ""  # Unique identifier
        self._controller = output_controller
        self._controller.canUpdateFirmwareChanged.connect(self._onControllerCanUpdateFirmwareChanged)
        self._extruders = [ExtruderOutputModel(printer = self, position = i) for i in range(number_of_extruders)]
        self._printer_configuration = PrinterConfigurationModel()  # Indicates the current configuration setup in this printer
        self._head_position = Vector(0, 0, 0)
        self._active_print_job = None  # type: Optional[PrintJobOutputModel]
        self._firmware_version = firmware_version
        self._printer_state = "unknown"
        self._is_preheating = False
        self._printer_type = ""
        self._buildplate = ""

        self._printer_configuration.extruderConfigurations = [extruder.extruderConfiguration for extruder in
                                                              self._extruders]

        self._camera_url = QUrl()  # type: QUrl

    @pyqtProperty(str, constant = True)
    def firmwareVersion(self) -> str:
        return self._firmware_version

    def setCameraUrl(self, camera_url: "QUrl") -> None:
        if self._camera_url != camera_url:
            self._camera_url = camera_url
            self.cameraUrlChanged.emit()

    @pyqtProperty(QUrl, fset = setCameraUrl, notify = cameraUrlChanged)
    def cameraUrl(self) -> "QUrl":
        return self._camera_url

    def updateIsPreheating(self, pre_heating: bool) -> None:
        if self._is_preheating != pre_heating:
            self._is_preheating = pre_heating
            self.isPreheatingChanged.emit()

    @pyqtProperty(bool, notify=isPreheatingChanged)
    def isPreheating(self) -> bool:
        return self._is_preheating

    @pyqtProperty(str, notify = typeChanged)
    def type(self) -> str:
        return self._printer_type

    def updateType(self, printer_type: str) -> None:
        if self._printer_type != printer_type:
            self._printer_type = printer_type
            self._printer_configuration.printerType = self._printer_type
            self.typeChanged.emit()
            self.configurationChanged.emit()

    @pyqtProperty(str, notify = buildplateChanged)
    def buildplate(self) -> str:
        return self._buildplate

    def updateBuildplate(self, buildplate: str) -> None:
        if self._buildplate != buildplate:
            self._buildplate = buildplate
            self._printer_configuration.buildplateConfiguration = self._buildplate
            self.buildplateChanged.emit()
            self.configurationChanged.emit()

    @pyqtProperty(str, notify=keyChanged)
    def key(self) -> str:
        return self._key

    def updateKey(self, key: str) -> None:
        if self._key != key:
            self._key = key
            self.keyChanged.emit()

    @pyqtSlot()
    def homeHead(self) -> None:
        self._controller.homeHead(self)

    @pyqtSlot()
    def homeBed(self) -> None:
        self._controller.homeBed(self)

    @pyqtSlot(str)
    def sendRawCommand(self, command: str) -> None:
        self._controller.sendRawCommand(self, command)

    @pyqtProperty("QVariantList", constant = True)
    def extruders(self) -> List["ExtruderOutputModel"]:
        return self._extruders

    @pyqtProperty(QVariant, notify = headPositionChanged)
    def headPosition(self) -> Dict[str, float]:
        return {"x": self._head_position.x, "y": self._head_position.y, "z": self.head_position.z}

    def updateHeadPosition(self, x: float, y: float, z: float) -> None:
        if self._head_position.x != x or self._head_position.y != y or self._head_position.z != z:
            self._head_position = Vector(x, y, z)
            self.headPositionChanged.emit()

    @pyqtProperty(float, float, float)
    @pyqtProperty(float, float, float, float)
    def setHeadPosition(self, x: float, y: float, z: float, speed: float = 3000) -> None:
        self.updateHeadPosition(x, y, z)
        self._controller.setHeadPosition(self, x, y, z, speed)

    @pyqtProperty(float)
    @pyqtProperty(float, float)
    def setHeadX(self, x: float, speed: float = 3000) -> None:
        self.updateHeadPosition(x, self._head_position.y, self._head_position.z)
        self._controller.setHeadPosition(self, x, self._head_position.y, self._head_position.z, speed)

    @pyqtProperty(float)
    @pyqtProperty(float, float)
    def setHeadY(self, y: float, speed: float = 3000) -> None:
        self.updateHeadPosition(self._head_position.x, y, self._head_position.z)
        self._controller.setHeadPosition(self, self._head_position.x, y, self._head_position.z, speed)

    @pyqtProperty(float)
    @pyqtProperty(float, float)
    def setHeadZ(self, z: float, speed:float = 3000) -> None:
        self.updateHeadPosition(self._head_position.x, self._head_position.y, z)
        self._controller.setHeadPosition(self, self._head_position.x, self._head_position.y, z, speed)

    @pyqtSlot(float, float, float)
    @pyqtSlot(float, float, float, float)
    def moveHead(self, x: float = 0, y: float = 0, z: float = 0, speed: float = 3000) -> None:
        self._controller.moveHead(self, x, y, z, speed)

    ##  Pre-heats the heated bed of the printer.
    #
    #   \param temperature The temperature to heat the bed to, in degrees
    #   Celsius.
    #   \param duration How long the bed should stay warm, in seconds.
    @pyqtSlot(float, float)
    def preheatBed(self, temperature: float, duration: float) -> None:
        self._controller.preheatBed(self, temperature, duration)

    @pyqtSlot()
    def cancelPreheatBed(self) -> None:
        self._controller.cancelPreheatBed(self)

    def getController(self) -> "PrinterOutputController":
        return self._controller

    @pyqtProperty(str, notify = nameChanged)
    def name(self) -> str:
        return self._name

    def setName(self, name: str) -> None:
        self.updateName(name)

    def updateName(self, name: str) -> None:
        if self._name != name:
            self._name = name
            self.nameChanged.emit()

    ##  Update the bed temperature. This only changes it locally.
    def updateBedTemperature(self, temperature: float) -> None:
        if self._bed_temperature != temperature:
            self._bed_temperature = temperature
            self.bedTemperatureChanged.emit()

    def updateTargetBedTemperature(self, temperature: float) -> None:
        if self._target_bed_temperature != temperature:
            self._target_bed_temperature = temperature
            self.targetBedTemperatureChanged.emit()

    ##  Set the target bed temperature. This ensures that it's actually sent to the remote.
    @pyqtSlot(float)
    def setTargetBedTemperature(self, temperature: float) -> None:
        self._controller.setTargetBedTemperature(self, temperature)
        self.updateTargetBedTemperature(temperature)

    def updateActivePrintJob(self, print_job: Optional["PrintJobOutputModel"]) -> None:
        if self._active_print_job != print_job:
            old_print_job = self._active_print_job

            if print_job is not None:
                print_job.updateAssignedPrinter(self)
            self._active_print_job = print_job

            if old_print_job is not None:
                old_print_job.updateAssignedPrinter(None)
            self.activePrintJobChanged.emit()

    def updateState(self, printer_state: str) -> None:
        if self._printer_state != printer_state:
            self._printer_state = printer_state
            self.stateChanged.emit()

    @pyqtProperty(QObject, notify = activePrintJobChanged)
    def activePrintJob(self) -> Optional["PrintJobOutputModel"]:
        return self._active_print_job

    @pyqtProperty(str, notify = stateChanged)
    def state(self) -> str:
        return self._printer_state

    @pyqtProperty(float, notify = bedTemperatureChanged)
    def bedTemperature(self) -> float:
        return self._bed_temperature

    @pyqtProperty(float, notify = targetBedTemperatureChanged)
    def targetBedTemperature(self) -> float:
        return self._target_bed_temperature

    # Does the printer support pre-heating the bed at all
    @pyqtProperty(bool, constant = True)
    def canPreHeatBed(self) -> bool:
        if self._controller:
            return self._controller.can_pre_heat_bed
        return False

    # Does the printer support pre-heating the bed at all
    @pyqtProperty(bool, constant = True)
    def canPreHeatHotends(self) -> bool:
        if self._controller:
            return self._controller.can_pre_heat_hotends
        return False

    # Does the printer support sending raw G-code at all
    @pyqtProperty(bool, constant = True)
    def canSendRawGcode(self) -> bool:
        if self._controller:
            return self._controller.can_send_raw_gcode
        return False

    # Does the printer support pause at all
    @pyqtProperty(bool, constant = True)
    def canPause(self) -> bool:
        if self._controller:
            return self._controller.can_pause
        return False

    # Does the printer support abort at all
    @pyqtProperty(bool, constant = True)
    def canAbort(self) -> bool:
        if self._controller:
            return self._controller.can_abort
        return False

    # Does the printer support manual control at all
    @pyqtProperty(bool, constant = True)
    def canControlManually(self) -> bool:
        if self._controller:
            return self._controller.can_control_manually
        return False

    # Does the printer support upgrading firmware
    @pyqtProperty(bool, notify = canUpdateFirmwareChanged)
    def canUpdateFirmware(self) -> bool:
        if self._controller:
            return self._controller.can_update_firmware
        return False

    # Stub to connect UM.Signal to pyqtSignal
    def _onControllerCanUpdateFirmwareChanged(self) -> None:
        self.canUpdateFirmwareChanged.emit()

    # Returns the configuration (material, variant and buildplate) of the current printer
    @pyqtProperty(QObject, notify = configurationChanged)
    def printerConfiguration(self) -> Optional[PrinterConfigurationModel]:
        if self._printer_configuration.isValid():
            return self._printer_configuration
        return None