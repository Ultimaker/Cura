# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import List, Optional

from PyQt5.QtCore import pyqtProperty, pyqtSignal
from PyQt5.QtGui import QImage
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest

from UM.Logger import Logger
from UM.TaskManagement.HttpRequestManager import HttpRequestManager
from cura.PrinterOutput.Models.PrintJobOutputModel import PrintJobOutputModel
from cura.PrinterOutput.PrinterOutputController import PrinterOutputController

from .ConfigurationChangeModel import ConfigurationChangeModel


class UM3PrintJobOutputModel(PrintJobOutputModel):
    configurationChangesChanged = pyqtSignal()

    def __init__(self, output_controller: PrinterOutputController, key: str = "", name: str = "", parent=None) -> None:
        super().__init__(output_controller, key, name, parent)
        self._configuration_changes = []  # type: List[ConfigurationChangeModel]

    @pyqtProperty("QVariantList", notify=configurationChangesChanged)
    def configurationChanges(self) -> List[ConfigurationChangeModel]:
        return self._configuration_changes

    def updateConfigurationChanges(self, changes: List[ConfigurationChangeModel]) -> None:
        if len(self._configuration_changes) == 0 and len(changes) == 0:
            return
        self._configuration_changes = changes
        self.configurationChangesChanged.emit()

    def updatePreviewImageData(self, data: bytes) -> None:
        image = QImage()
        image.loadFromData(data)
        self.updatePreviewImage(image)

    def loadPreviewImageFromUrl(self, url: str) -> None:
        HttpRequestManager.getInstance().get(url=url, callback=self._onImageLoaded, error_callback=self._onImageLoaded)

    def _onImageLoaded(self, reply: QNetworkReply, error: Optional["QNetworkReply.NetworkError"] = None) -> None:
        if not HttpRequestManager.replyIndicatesSuccess(reply, error):
            Logger.warning("Requesting preview image failed, response code {0} while trying to connect to {1}".format(
                           reply.attribute(QNetworkRequest.HttpStatusCodeAttribute), reply.url()))
            return
        self.updatePreviewImageData(reply.readAll())
