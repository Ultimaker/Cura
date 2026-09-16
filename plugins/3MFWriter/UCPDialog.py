# Copyright (c) 2024 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os

from PyQt6.QtCore import pyqtSignal, QObject

import UM
from UM.FlameProfiler import pyqtSlot
from UM.OutputDevice import OutputDeviceError
from UM.Workspace.WorkspaceWriter import WorkspaceWriter
from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Message import Message

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
        self._view = CuraApplication.getInstance().createQmlComponent(
            dialog_path,
            {
                "manager": self,
                "settingsExportModel": self._model
            }
        )
        self._view.accepted.connect(self._onAccepted)
        self._view.rejected.connect(self._onRejected)
        self._finished = False
        self._accepted = False

    def show(self) -> None:
        self._finished = False
        self._accepted = False
        self._view.show()

    def getModel(self) -> SettingsExportModel:
        return self._model

    @pyqtSlot()
    def notifyClosed(self):
        self._onFinished()

    def save3mf(self):
        application = CuraApplication.getInstance()
        workspace_handler = application.getInstance().getWorkspaceFileHandler()

        # Set the model to the workspace writer
        mesh_writer = workspace_handler.getWriter("3MFWriter")
        mesh_writer.setExportModel(self._model)

        # Open file dialog and write the file
        device = application.getOutputDeviceManager().getOutputDevice("local_file")
        nodes = [application.getController().getScene().getRoot()]

        device.writeError.connect(lambda: self._onRejected())
        device.writeSuccess.connect(lambda: self._onSuccess())
        device.writeFinished.connect(lambda: self._onFinished())

        file_name = f"UCP_{CuraApplication.getInstance().getPrintInformation().baseName}"

        try:
            device.requestWrite(
                nodes,
                file_name,
                ["application/x-ucp"],
                workspace_handler,
                preferred_mimetype_list="application/x-ucp"
            )
        except OutputDeviceError.UserCanceledError:
            self._onRejected()
        except Exception as e:
            message = Message(
                i18n_catalog.i18nc("@info:error", "Unable to write to file: {0}", file_name),
                title=i18n_catalog.i18nc("@info:title", "Error"),
                message_type=Message.MessageType.ERROR
            )
            message.show()
            Logger.logException("e", "Unable to write to file %s: %s", file_name, e)
            self._onRejected()

    def _onAccepted(self):
        self.save3mf()

    def _onRejected(self):
        self._onFinished()

    def _onSuccess(self):
        self._accepted = True
        self._onFinished()

    def _onFinished(self):
        # Make sure we don't send the finished signal twice, whatever happens
        if self._finished:
            return
        self._finished = True

        # Reset the model to the workspace writer
        mesh_writer = CuraApplication.getInstance().getInstance().getWorkspaceFileHandler().getWriter("3MFWriter")
        mesh_writer.setExportModel(None)

        self.finished.emit(self._accepted)
