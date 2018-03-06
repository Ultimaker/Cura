# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty, QObject, pyqtSignal


class ExtruderConfigurationModel(QObject):

    extruderConfigurationChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._position = -1
        self._material = None
        self._hotend_id = None

    def setPosition(self, position):
        self._position = position

    @pyqtProperty(int, fset = setPosition, notify = extruderConfigurationChanged)
    def position(self):
        return self._position

    def setMaterial(self, material):
        self._material = material

    @pyqtProperty(str, fset = setMaterial, notify = extruderConfigurationChanged)
    def material(self):
        return self._material

    def setHotendID(self, hotend_id):
        self._hotend_id = hotend_id

    @pyqtProperty(str, fset = setHotendID, notify = extruderConfigurationChanged)
    def hotendID(self):
        return self._hotend_id

    def __str__(self):
        if self._material is None or self._hotend_id is None:
            return "No information"
        return "Position: " + str(self._position) + " - Material: " + self._material + " - HotendID: " + self._hotend_id

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash(self._position) ^ hash(self._material) ^ hash(self._hotend_id)