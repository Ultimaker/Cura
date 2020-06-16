# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, TYPE_CHECKING

from PyQt5.QtCore import pyqtSignal, pyqtProperty, QObject, pyqtSlot

from .ExtruderConfigurationModel import ExtruderConfigurationModel

if TYPE_CHECKING:
    from .MaterialOutputModel import MaterialOutputModel
    from .PrinterOutputModel import PrinterOutputModel


class ExtruderOutputModel(QObject):
    targetHotendTemperatureChanged = pyqtSignal()
    hotendTemperatureChanged = pyqtSignal()

    extruderConfigurationChanged = pyqtSignal()
    isPreheatingChanged = pyqtSignal()

    def __init__(self, printer: "PrinterOutputModel", position: int, parent=None) -> None:
        super().__init__(parent)
        self._printer = printer  # type: PrinterOutputModel
        self._position = position
        self._target_hotend_temperature = 0.0  # type: float
        self._hotend_temperature = 0.0  # type: float

        self._is_preheating = False

        # The extruder output model wraps the configuration model. This way we can use the same config model for jobs
        # and extruders alike.
        self._extruder_configuration = ExtruderConfigurationModel()
        self._extruder_configuration.position = self._position
        self._extruder_configuration.extruderConfigurationChanged.connect(self.extruderConfigurationChanged)

    def getPrinter(self) -> "PrinterOutputModel":
        return self._printer

    def getPosition(self) -> int:
        return self._position

    # Does the printer support pre-heating the bed at all
    @pyqtProperty(bool, constant=True)
    def canPreHeatHotends(self) -> bool:
        if self._printer:
            return self._printer.canPreHeatHotends
        return False

    @pyqtProperty(QObject, notify = extruderConfigurationChanged)
    def activeMaterial(self) -> Optional["MaterialOutputModel"]:
        return self._extruder_configuration.activeMaterial

    def updateActiveMaterial(self, material: Optional["MaterialOutputModel"]) -> None:
        self._extruder_configuration.setMaterial(material)

    def updateHotendTemperature(self, temperature: float) -> None:
        """Update the hotend temperature. This only changes it locally."""

        if self._hotend_temperature != temperature:
            self._hotend_temperature = temperature
            self.hotendTemperatureChanged.emit()

    def updateTargetHotendTemperature(self, temperature: float) -> None:
        if self._target_hotend_temperature != temperature:
            self._target_hotend_temperature = temperature
            self.targetHotendTemperatureChanged.emit()

    @pyqtSlot(float)
    def setTargetHotendTemperature(self, temperature: float) -> None:
        """Set the target hotend temperature. This ensures that it's actually sent to the remote."""

        self._printer.getController().setTargetHotendTemperature(self._printer, self, temperature)
        self.updateTargetHotendTemperature(temperature)

    @pyqtProperty(float, notify = targetHotendTemperatureChanged)
    def targetHotendTemperature(self) -> float:
        return self._target_hotend_temperature

    @pyqtProperty(float, notify = hotendTemperatureChanged)
    def hotendTemperature(self) -> float:
        return self._hotend_temperature

    @pyqtProperty(str, notify = extruderConfigurationChanged)
    def hotendID(self) -> str:
        return self._extruder_configuration.hotendID

    def updateHotendID(self, hotend_id: str) -> None:
        self._extruder_configuration.setHotendID(hotend_id)

    @pyqtProperty(QObject, notify = extruderConfigurationChanged)
    def extruderConfiguration(self) -> Optional[ExtruderConfigurationModel]:
        if self._extruder_configuration.isValid():
            return self._extruder_configuration
        return None

    def updateIsPreheating(self, pre_heating: bool) -> None:
        if self._is_preheating != pre_heating:
            self._is_preheating = pre_heating
            self.isPreheatingChanged.emit()

    @pyqtProperty(bool, notify=isPreheatingChanged)
    def isPreheating(self) -> bool:
        return self._is_preheating

    @pyqtSlot(float, float)
    def preheatHotend(self, temperature: float, duration: float) -> None:
        """Pre-heats the extruder before printer.

        :param temperature: The temperature to heat the extruder to, in degrees
            Celsius.
        :param duration: How long the bed should stay warm, in seconds.
        """

        self._printer._controller.preheatHotend(self, temperature, duration)

    @pyqtSlot()
    def cancelPreheatHotend(self) -> None:
        self._printer._controller.cancelPreheatHotend(self)
