#  Copyright (c) 2024 Ultimaker B.V.
#  Cura is released under the terms of the LGPLv3 or higher.

from PyQt6.QtCore import Qt, QObject, pyqtProperty
from UM.FlameProfiler import pyqtSlot
from UM.Application import Application
from UM.Qt.ListModel import ListModel
from UM.Logger import Logger


class SettingsExport():

    def __init__(self):
        super().__init__()
        self._name = "Generate Support"
        self._value = "Enabled"

    @pyqtProperty(str, constant=True)
    def name(self):
        return self._name

    @pyqtProperty(str, constant=True)
    def value(self):
        return self._value
