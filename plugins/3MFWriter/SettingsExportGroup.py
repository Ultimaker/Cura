#  Copyright (c) 2024 Ultimaker B.V.
#  Cura is released under the terms of the LGPLv3 or higher.

from enum import IntEnum

from PyQt6.QtCore import QObject, pyqtProperty, pyqtEnum


class SettingsExportGroup(QObject):

    @pyqtEnum
    class Category(IntEnum):
        Global = 0
        Extruder = 1
        Model = 2

    def __init__(self, stack, name, category, settings, category_details = '', extruder_index = 0, extruder_color = ''):
        super().__init__()
        self.stack = stack
        self._name = name
        self._settings = settings
        self._category = category
        self._category_details = category_details
        self._extruder_index = extruder_index
        self._extruder_color = extruder_color
        self._visible_settings = []

    @pyqtProperty(str, constant=True)
    def name(self):
        return self._name

    @pyqtProperty(list, constant=True)
    def settings(self):
        return self._settings

    @pyqtProperty(list, constant=True)
    def visibleSettings(self):
        if self._visible_settings == []:
            self._visible_settings = list(filter(lambda item : item.isVisible, self._settings))
        return self._visible_settings

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
