# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import QObject
from UM.PluginObject import PluginObject


class MachineAction(QObject, PluginObject):
    def __init__(self, key, label = ""):
        super().__init__()
        self._key = key
        self._label = label

    def getKey(self):
        return self._key

    def getLabel(self):
        return self._label
