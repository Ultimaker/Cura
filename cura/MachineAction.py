from PyQt5.QtCore import QObject
from UM.PluginObject import PluginObject


class MachineAction(QObject, PluginObject):
    def __init__(self, key, label = ""):
        self._key = key
        self._label = label
