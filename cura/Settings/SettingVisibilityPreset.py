import os
import urllib.parse
from configparser import ConfigParser
from typing import List

from PyQt5.QtCore import pyqtProperty, QObject, pyqtSignal

from UM.Logger import Logger
from UM.MimeTypeDatabase import MimeTypeDatabase, MimeTypeNotFoundError


class SettingVisibilityPreset(QObject):
    onSettingsChanged = pyqtSignal()
    onNameChanged = pyqtSignal()
    onWeightChanged = pyqtSignal()
    onIdChanged = pyqtSignal()

    def __init__(self, id: str = "", name: str = "" , weight: int = 0, parent = None) -> None:
        super().__init__(parent)
        self._settings = []  # type: List[str]
        self._id = id
        self._weight = weight
        self._name = name

    @pyqtProperty("QStringList", notify = onSettingsChanged)
    def settings(self) -> List[str]:
        return self._settings

    @pyqtProperty(str, notify=onIdChanged)
    def id(self) -> str:
        return self._id

    @pyqtProperty(int, notify=onWeightChanged)
    def weight(self) -> int:
        return self._weight

    @pyqtProperty(str, notify=onNameChanged)
    def name(self) -> str:
        return self._name

    def setName(self, name: str) -> None:
        if name != self._name:
            self._name = name
            self.onNameChanged.emit()

    def setId(self, id: int) -> None:
        if id != self._id:
            self._id = id
            self.onIdChanged.emit()

    def setWeight(self, weight: str) -> None:
        if weight != self._weight:
            self._weight = weight
            self.onWeightChanged.emit()

    def setSettings(self, settings: List[str]) -> None:
        if set(settings) != set(self._settings):
            self._settings = list(set(settings))  # filter out non unique
            self.onSettingsChanged.emit()

    def loadFromFile(self, file_path: str) -> None:
        mime_type = MimeTypeDatabase.getMimeTypeForFile(file_path)

        item_id = urllib.parse.unquote_plus(mime_type.stripExtension(os.path.basename(file_path)))
        if not os.path.isfile(file_path):
            Logger.log("e", "[%s] is not a file", file_path)
            return None

        parser = ConfigParser(allow_no_value=True)  # Accept options without any value,

        parser.read([file_path])
        if not parser.has_option("general", "name") or not parser.has_option("general", "weight"):
            return None

        settings = []  # type: List[str]
        for section in parser.sections():
            if section == "general":
                continue

            settings.append(section)
            for option in parser[section].keys():
                settings.append(option)
        self.setSettings(settings)
        self.setId(item_id)
        self.setName(parser["general"]["name"])
        self.setWeight(parser["general"]["weight"])

