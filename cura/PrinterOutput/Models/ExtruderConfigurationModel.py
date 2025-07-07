# Copyright (c) 2024 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional

from PyQt6.QtCore import pyqtProperty, QObject, pyqtSignal

from cura.PrinterOutput.FormatMaps import FormatMaps
from .MaterialOutputModel import MaterialOutputModel


class ExtruderConfigurationModel(QObject):

    extruderConfigurationChanged = pyqtSignal()

    def __init__(self, position: int = -1) -> None:
        super().__init__()
        self._position: int = position
        self._material: Optional[MaterialOutputModel] = None
        self._hotend_id: Optional[str] = None

    def setPosition(self, position: int) -> None:
        self._position = position

    @pyqtProperty(int, fset = setPosition, notify = extruderConfigurationChanged)
    def position(self) -> int:
        return self._position

    def setMaterial(self, material: Optional[MaterialOutputModel]) -> None:
        if material is None or self._material == material:
            return
        self._material = material
        self.extruderConfigurationChanged.emit()

    @pyqtProperty(QObject, fset = setMaterial, notify = extruderConfigurationChanged)
    def activeMaterial(self) -> Optional[MaterialOutputModel]:
        return self._material

    @pyqtProperty(QObject, fset = setMaterial, notify = extruderConfigurationChanged)
    def material(self) -> Optional[MaterialOutputModel]:
        return self._material

    def setHotendID(self, hotend_id: Optional[str]) -> None:
        if self._hotend_id != hotend_id:
            self._hotend_id = ExtruderConfigurationModel.applyNameMappingHotend(hotend_id)
            self.extruderConfigurationChanged.emit()

    @staticmethod
    def applyNameMappingHotend(hotendId) -> str:
        if hotendId in FormatMaps.EXTRUDER_NAME_MAP:
            return FormatMaps.EXTRUDER_NAME_MAP[hotendId]
        return hotendId

    @pyqtProperty(str, fset = setHotendID, notify = extruderConfigurationChanged)
    def hotendID(self) -> Optional[str]:
        return self._hotend_id

    def isValid(self) -> bool:
        """This method is intended to indicate whether the configuration is valid or not.

        The method checks if the mandatory fields are or not set
        At this moment is always valid since we allow to have empty material and variants.
        """

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
        if not isinstance(other, ExtruderConfigurationModel):
            return False

        if self._position != other.position:
            return False
        # Empty materials should be ignored for comparison
        if self.activeMaterial is not None and other.activeMaterial is not None:
            if self.activeMaterial.guid != other.activeMaterial.guid:
                if self.activeMaterial.guid == "" and other.activeMaterial.guid == "":
                    # At this point there is no material, so it doesn't matter what the hotend is.
                    return True
                else:
                    return False

        if self.hotendID != other.hotendID:
            return False

        return True

    #   Calculating a hash function using the position of the extruder, the material GUID and the hotend id to check if is
    #   unique within a set
    def __hash__(self):
        return hash(self._position) ^ (hash(self._material.guid) if self._material is not None else hash(0)) ^ hash(self._hotend_id)
