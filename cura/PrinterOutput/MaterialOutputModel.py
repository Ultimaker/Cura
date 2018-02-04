# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtSignal, pyqtProperty, QObject, QVariant, pyqtSlot


class MaterialOutputModel(QObject):
    def __init__(self, guid, type, color, brand, name, parent = None):
        super().__init__(parent)
        self._guid = guid
        self._type = type
        self._color = color
        self._brand = brand
        self._name = name

    @pyqtProperty(str, constant = True)
    def guid(self):
        return self._guid

    @pyqtProperty(str, constant=True)
    def type(self):
        return self._type

    @pyqtProperty(str, constant=True)
    def brand(self):
        return self._brand

    @pyqtProperty(str, constant=True)
    def color(self):
        return self._color

    @pyqtProperty(str, constant=True)
    def name(self):
        return self._name