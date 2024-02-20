# Copyright (c) 2024 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os

from PyQt6.QtCore import pyqtSignal, QObject

import UM
from UM.FlameProfiler import pyqtSlot
from UM.i18n import i18nCatalog

from cura.CuraApplication import CuraApplication

from .SettingsExportModel import SettingsExportModel

i18n_catalog = i18nCatalog("cura")


class UCPDialog(QObject):
    finished = pyqtSignal(bool)

    def __init__(self, parent = None) -> None:
        super().__init__(parent)

        plugin_path = os.path.dirname(__file__)
        dialog_path = os.path.join(plugin_path, 'UCPDialog.qml')
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
        mesh_writer = CuraApplication.getInstance().getMeshFileHandler().getWriter("3MFWriter")
        mesh_writer.custom_data = "My custom data"

        device = CuraApplication.getInstance().getOutputDeviceManager().getOutputDevice("local_file")
        file_handler = UM.Qt.QtApplication.QtApplication.getInstance().getWorkspaceFileHandler()
        nodes = [CuraApplication.getInstance().getController().getScene().getRoot()]
        device.requestWrite(nodes, "test.3mf", ["application/x-ucp"], file_handler,
                            preferred_mimetype_list="application/x-ucp")
        #TODO: update _export_model in threeMFWorkspacewriter and set is_ucp is true
        # = self._config_dialog.getModel()
        self._onFinished()

    @pyqtSlot()
    def _onRejected(self):
        self._onFinished()

    def _onFinished(self):
        if not self._finished: # Make sure we don't send the finished signal twice, whatever happens
            self._finished = True
            self.finished.emit(self._accepted)
