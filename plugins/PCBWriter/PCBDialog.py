# Copyright (c) 2024 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os

from PyQt6.QtCore import pyqtSignal, QObject
from UM.FlameProfiler import pyqtSlot
from UM.i18n import i18nCatalog

from cura.CuraApplication import CuraApplication

from .SettingsExportModel import SettingsExportModel

i18n_catalog = i18nCatalog("cura")


class PCBDialog(QObject):
    finished = pyqtSignal(bool)

    def __init__(self, parent = None) -> None:
        super().__init__(parent)

        plugin_path = os.path.dirname(__file__)
        dialog_path = os.path.join(plugin_path, 'PCBDialog.qml')
        self._model = SettingsExportModel()
        self._view = CuraApplication.getInstance().createQmlComponent(dialog_path,
                                                                      {"manager": self,
                                                                       "settingsExportModel": self._model})
        self._view.accepted.connect(self._onAccepted)
        self._view.rejected.connect(self._onRejected)
        self._finished = False
        self._accepted = False

    def show(self) -> None:
        self._view.show()

    def getModel(self) -> SettingsExportModel:
        return self._model

    @pyqtSlot()
    def notifyClosed(self):
        self._onFinished()

    @pyqtSlot()
    def _onAccepted(self):
        self._accepted = True
        self._onFinished()

    @pyqtSlot()
    def _onRejected(self):
        self._onFinished()

    def _onFinished(self):
        if not self._finished: # Make sure we don't send the finished signal twice, whatever happens
            self._finished = True
            self.finished.emit(self._accepted)
