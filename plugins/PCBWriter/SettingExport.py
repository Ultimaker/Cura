#  Copyright (c) 2024 Ultimaker B.V.
#  Cura is released under the terms of the LGPLv3 or higher.

from PyQt6.QtCore import QObject, pyqtProperty


class SettingsExport(QObject):

    def __init__(self, name, value):
        super().__init__()
        self._name = name
        self._value = value

    @pyqtProperty(str, constant=True)
    def name(self):
        return self._name

    @pyqtProperty(str, constant=True)
    def value(self):
        return self._value
