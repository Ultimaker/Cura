# Copyright ;(c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import QTimer

from UM.Extension import Extension
from UM.Application import Application
from UM.PluginRegistry import PluginRegistry
from UM.Logger import Logger

from UM.Backend.Backend import BackendState

from PyQt5.QtQml import QQmlComponent, QQmlContext
from PyQt5.QtCore import QUrl, pyqtSlot, QObject

import os.path

class PauseBackend(QObject, Extension):
    def __init__(self, parent = None):
        super().__init__(parent = parent)

        self._additional_component = None
        self._additional_components_view = None

        Application.getInstance().engineCreatedSignal.connect(self._createAdditionalComponentsView)

    def _createAdditionalComponentsView(self):
        Logger.log("d", "Creating additional ui components for Pause Backend plugin.")

        path = QUrl.fromLocalFile(os.path.join(PluginRegistry.getInstance().getPluginPath("PauseBackendPlugin"), "PauseBackend.qml"))
        self._additional_component = QQmlComponent(Application.getInstance()._engine, path)

        # We need access to engine (although technically we can't)
        self._additional_components_context = QQmlContext(Application.getInstance()._engine.rootContext())
        self._additional_components_context.setContextProperty("manager", self)

        self._additional_components_view = self._additional_component.create(self._additional_components_context)
        if not self._additional_components_view:
            Logger.log("w", "Could not create additional components for Pause Backend plugin.")
            return

        Application.getInstance().addAdditionalComponent("saveButton", self._additional_components_view.findChild(QObject, "pauseResumeButton"))

    @pyqtSlot()
    def pauseBackend(self):
        backend = Application.getInstance().getBackend()
        backend.pauseSlicing()

    @pyqtSlot()
    def resumeBackend(self):
        backend = Application.getInstance().getBackend()
        backend.continueSlicing()
        backend.forceSlice()