#  Copyright (c) 2024 Ultimaker B.V.
#  Cura is released under the terms of the LGPLv3 or higher.

from enum import IntEnum

from PyQt6.QtCore import Qt, QObject, pyqtProperty, pyqtEnum
from UM.FlameProfiler import pyqtSlot
from UM.Application import Application
from UM.Qt.ListModel import ListModel
from UM.Logger import Logger

from .SettingExport import SettingsExport


class SettingsExportGroup(QObject):

    @pyqtEnum
    class Category(IntEnum):
        Global = 0
        Extruder = 1
        Model = 2

    def __init__(self, name, category, category_details = '', extruder_index = 0, extruder_color = ''):
        super().__init__()
        self._name = name
        self._settings = []
        self._category = category
        self._category_details = category_details
        self._extruder_index = extruder_index
        self._extruder_color = extruder_color
        self._updateSettings()

    @pyqtProperty(str, constant=True)
    def name(self):
        return self._name

    @pyqtProperty(list, constant=True)
    def settings(self):
        return self._settings

    @pyqtProperty(int, constant=True)
    def category(self):
        return self._category

    @pyqtProperty(str, constant=True)
    def category_details(self):
        return self._category_details

    @pyqtProperty(int, constant=True)
    def extruder_index(self):
        return self._extruder_index

    @pyqtProperty(str, constant=True)
    def extruder_color(self):
        return self._extruder_color

    def _updateSettings(self):
        self._settings.append(SettingsExport())
        self._settings.append(SettingsExport())