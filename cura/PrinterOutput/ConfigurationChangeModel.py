
from PyQt5.QtCore import pyqtSignal, pyqtProperty, QObject, pyqtSlot


class ConfigurationChangeModel(QObject):
    def __init__(self, type_of_change: str, index: int, target_name: str, origin_name: str) -> None:
        super().__init__()
        self._type_of_change = type_of_change
                                    # enum = ["material", "print_core_change"]
        self._index = index
        self._target_name = target_name
        self._origin_name = origin_name

    @pyqtProperty(int)
    def index(self) -> int:
        return self._index
    # "target_id": fields.String(required=True, description="Target material guid or hotend id"),
    # "origin_id": fields.String(required=True, description="Original/current material guid or hotend id"),

    @pyqtProperty(str)
    def typeOfChange(self) -> str:
        return self._type_of_change

    @pyqtProperty(str)
    def targetName(self) -> str:
        return self._target_name

    @pyqtProperty(str)
    def originName(self) -> str:
        return self._origin_name
