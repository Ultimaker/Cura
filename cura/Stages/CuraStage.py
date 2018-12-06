# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from PyQt5.QtCore import pyqtProperty, QUrl

from UM.Stage import Stage


class CuraStage(Stage):

    def __init__(self, parent = None):
        super().__init__(parent)

    @pyqtProperty(str, constant = True)
    def stageId(self):
        return self.getPluginId()

    @pyqtProperty(QUrl, constant = True)
    def mainComponent(self):
        return self.getDisplayComponent("main")

    @pyqtProperty(QUrl, constant = True)
    def sidebarComponent(self):
        return self.getDisplayComponent("sidebar")
