# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from PyQt5.QtCore import pyqtProperty, QObject


BLOCKING_CHANGE_TYPES = [
    "material_insert", "buildplate_change"
]


class ConfigurationChangeModel(QObject):
    def __init__(self, type_of_change: str, index: int, target_name: str, origin_name: str) -> None:
        super().__init__()
        self._type_of_change = type_of_change  # enum = ["material", "print_core_change"]
        self._can_override = self._type_of_change not in BLOCKING_CHANGE_TYPES
        self._index = index
        self._target_name = target_name
        self._origin_name = origin_name

    @pyqtProperty(int, constant = True)
    def index(self) -> int:
        return self._index

    @pyqtProperty(str, constant = True)
    def typeOfChange(self) -> str:
        return self._type_of_change

    @pyqtProperty(str, constant = True)
    def targetName(self) -> str:
        return self._target_name

    @pyqtProperty(str, constant = True)
    def originName(self) -> str:
        return self._origin_name

    @pyqtProperty(bool, constant = True)
    def canOverride(self) -> bool:
        return self._can_override
