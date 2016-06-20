# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal
from UM.PluginObject import PluginObject


class MachineAction(QObject, PluginObject):
    def __init__(self, key, label = ""):
        super().__init__()
        self._key = key
        self._label = label

    labelChanged = pyqtSignal()

    def getKey(self):
        return self._key

    @pyqtProperty(str, notify = labelChanged)
    def label(self):
        return self._label

    def setLabel(self, label):
        if self._label != label:
            self._label = label
            self.labelChanged.emit()

    @pyqtSlot()
    def execute(self):
        self._execute()

    def _execute(self):
        raise NotImplementedError("Execute() must be implemented")