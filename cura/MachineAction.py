# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal, QUrl
from PyQt5.QtQml import QQmlComponent, QQmlContext

from UM.PluginObject import PluginObject
from UM.PluginRegistry import PluginRegistry

from UM.Application import Application

import os


class MachineAction(QObject, PluginObject):
    def __init__(self, key, label = ""):
        super().__init__()
        self._key = key
        self._label = label
        self._qml_url = ""

        self._component = None
        self._context = None
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
        self._component = None
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

    def _createViewFromQML(self):
        path = QUrl.fromLocalFile(
            os.path.join(PluginRegistry.getInstance().getPluginPath(self.getPluginId()), self._qml_url))
        self._component = QQmlComponent(Application.getInstance()._engine, path)
        self._context = QQmlContext(Application.getInstance()._engine.rootContext())
        self._context.setContextProperty("manager", self)
        self._view = self._component.create(self._context)

    @pyqtProperty(QObject, constant = True)
    def displayItem(self):
        if not self._component:
            self._createViewFromQML()

        return self._view