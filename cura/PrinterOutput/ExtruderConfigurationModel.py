# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional

from PyQt5.QtCore import pyqtProperty, QObject, pyqtSignal

from cura.PrinterOutput.MaterialOutputModel import MaterialOutputModel


class ExtruderConfigurationModel(QObject):

    extruderConfigurationChanged = pyqtSignal()

    def __init__(self, position: int = -1) -> None:
        super().__init__()
        self._position = position  # type: int
        self._material = None  # type: Optional[MaterialOutputModel]
        self._hotend_id = None  # type: Optional[str]

    def setPosition(self, position: int) -> None:
        self._position = position

    @pyqtProperty(int, fset = setPosition, notify = extruderConfigurationChanged)
    def position(self) -> int:
        return self._position

    def setMaterial(self, material: Optional[MaterialOutputModel]) -> None:
        if self._hotend_id != material:
            self._material = material
            self.extruderConfigurationChanged.emit()

    @pyqtProperty(QObject, fset = setMaterial, notify = extruderConfigurationChanged)
    def activeMaterial(self) -> Optional[MaterialOutputModel]:
        return self._material

    @pyqtProperty(QObject, fset=setMaterial, notify=extruderConfigurationChanged)
    def material(self) -> Optional[MaterialOutputModel]:
        return self._material

    def setHotendID(self, hotend_id: Optional[str]) -> None:
        if self._hotend_id != hotend_id:
            self._hotend_id = hotend_id
            self.extruderConfigurationChanged.emit()

    @pyqtProperty(str, fset = setHotendID, notify = extruderConfigurationChanged)
    def hotendID(self) -> Optional[str]:
        return self._hotend_id

    ##  This method is intended to indicate whether the configuration is valid or not.
    #   The method checks if the mandatory fields are or not set
    #   At this moment is always valid since we allow to have empty material and variants.
    def isValid(self) -> bool:
        return True

    def __str__(self) -> str:
        message_chunks = []
        message_chunks.append("Position: " + str(self._position))
        message_chunks.append("-")
        message_chunks.append("Material: " + self.activeMaterial.type if self.activeMaterial else "empty")
        message_chunks.append("-")
        message_chunks.append("HotendID: " + self.hotendID if self.hotendID else "empty")
        return " ".join(message_chunks)

    def __eq__(self, other) -> bool:
        return hash(self) == hash(other)

    #   Calculating a hash function using the position of the extruder, the material GUID and the hotend id to check if is
    #   unique within a set
    def __hash__(self):
        return hash(self._position) ^ (hash(self._material.guid) if self._material is not None else hash(0)) ^ hash(self._hotend_id)