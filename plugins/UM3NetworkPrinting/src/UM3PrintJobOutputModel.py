# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtSignal, pyqtProperty, QObject, pyqtSlot
from typing import Optional, TYPE_CHECKING, List
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QImage

from cura.PrinterOutput.PrintJobOutputModel import PrintJobOutputModel

from .ConfigurationChangeModel import ConfigurationChangeModel


class UM3PrintJobOutputModel(PrintJobOutputModel):
    configurationChangesChanged = pyqtSignal()

    def __init__(self, output_controller: "PrinterOutputController", key: str = "", name: str = "", parent=None) -> None:
        super().__init__(output_controller, key, name, parent)
        self._configuration_changes = []    # type: List[ConfigurationChangeModel]

    @pyqtProperty("QVariantList", notify=configurationChangesChanged)
    def configurationChanges(self) -> List[ConfigurationChangeModel]:
        return self._configuration_changes

    def updateConfigurationChanges(self, changes: List[ConfigurationChangeModel]) -> None:
        if len(self._configuration_changes) == 0 and len(changes) == 0:
            return
        self._configuration_changes = changes
        self.configurationChangesChanged.emit()
