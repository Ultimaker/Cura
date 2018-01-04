# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal

from UM.PluginObject import PluginObject
from UM.PluginRegistry import PluginRegistry
from UM.Application import Application

import os


##  Machine actions are actions that are added to a specific machine type. Examples of such actions are
#   updating the firmware, connecting with remote devices or doing bed leveling. A machine action can also have a
#   qml, which should contain a "Cura.MachineAction" item. When activated, the item will be displayed in a dialog
#   and this object will be added as "manager" (so all pyqtSlot() functions can be called by calling manager.func())
class MachineAction(QObject, PluginObject):

    ##  Create a new Machine action.
    #   \param key unique key of the machine action
    #   \param label Human readable label used to identify the machine action.
    def __init__(self, key, label = ""):
        super().__init__()
        self._key = key
        self._label = label
        self._qml_url = ""
        self._view = None
        self._finished = False

    labelChanged = pyqtSignal()
    onFinished = pyqtSignal()

    def getKey(self):
        return self._key

    @pyqtProperty(str, notify = labelChanged)
    def label(self):
        return self._label

    def setLabel(self, label):
        if self._label != label:
            self._label = label
            self.labelChanged.emit()

    ##  Reset the action to it's default state.
    #   This should not be re-implemented by child classes, instead re-implement _reset.
    #   /sa _reset
    @pyqtSlot()
    def reset(self):
        self._finished = False
        self._reset()

    ##  Protected implementation of reset.
    #   /sa reset()
    def _reset(self):
        pass

    @pyqtSlot()
    def setFinished(self):
        self._finished = True
        self._reset()
        self.onFinished.emit()

    @pyqtProperty(bool, notify = onFinished)
    def finished(self):
        return self._finished

    ##  Protected helper to create a view object based on provided QML.
    def _createViewFromQML(self):
        path = os.path.join(PluginRegistry.getInstance().getPluginPath(self.getPluginId()), self._qml_url)
        self._view = Application.getInstance().createQmlComponent(path, {"manager": self})

    @pyqtProperty(QObject, constant = True)
    def displayItem(self):
        if not self._view:
            self._createViewFromQML()
        return self._view
