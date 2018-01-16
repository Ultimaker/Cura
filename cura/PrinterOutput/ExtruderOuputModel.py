# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtSignal, pyqtProperty, QObject, QVariant, pyqtSlot
from UM.Logger import Logger

from typing import Optional

MYPY = False
if MYPY:
    from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel
    from cura.PrinterOutput.MaterialOutputModel import MaterialOutputModel


class ExtruderOutputModel(QObject):
    hotendIDChanged = pyqtSignal()
    targetHotendTemperatureChanged = pyqtSignal()
    hotendTemperatureChanged = pyqtSignal()
    activeMaterialChanged = pyqtSignal()

    def __init__(self, printer: "PrinterOutputModel", parent=None):
        super().__init__(parent)
        self._printer = printer
        self._target_hotend_temperature = 0
        self._hotend_temperature = 0
        self._hotend_id = ""
        self._active_material = None  # type: Optional[MaterialOutputModel]

    @pyqtProperty(QObject, notify = activeMaterialChanged)
    def activeMaterial(self) -> "MaterialOutputModel":
        return self._active_material

    def updateActiveMaterial(self, material: Optional["MaterialOutputModel"]):
        if self._active_material != material:
            self._active_material = material
            self.activeMaterialChanged.emit()

    ##  Update the hotend temperature. This only changes it locally.
    def updateHotendTemperature(self, temperature: float):
        if self._hotend_temperature != temperature:
            self._hotend_temperature = temperature
            self.hotendTemperatureChanged.emit()

    def updateTargetHotendTemperature(self, temperature: float):
        if self._target_hotend_temperature != temperature:
            self._target_hotend_temperature = temperature
            self.targetHotendTemperatureChanged.emit()

    ##  Set the target hotend temperature. This ensures that it's actually sent to the remote.
    @pyqtSlot(float)
    def setTargetHotendTemperature(self, temperature: float):
        self._printer.getController().setTargetHotendTemperature(self._printer, self, temperature)
        self.updateTargetHotendTemperature(temperature)

    @pyqtProperty(float, notify = targetHotendTemperatureChanged)
    def targetHotendTemperature(self) -> float:
        return self._target_hotend_temperature

    @pyqtProperty(float, notify=hotendTemperatureChanged)
    def hotendTemperature(self) -> float:
        return self._hotend_temperature

    @pyqtProperty(str, notify = hotendIDChanged)
    def hotendID(self) -> str:
        return self._hotend_id

    def updateHotendID(self, id: str):
        if self._hotend_id != id:
            self._hotend_id = id
            self.hotendIDChanged.emit()
