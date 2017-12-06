# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from PyQt5.QtCore import pyqtProperty, QObject

from UM.Stage import Stage

class CuraStage(Stage):

    def __init__(self):
        super().__init__()

    @pyqtProperty(QObject, constant = True)
    def mainComponent(self):
        return self.getDisplayComponent("main")

    @pyqtProperty(QObject, constant = True)
    def sidebarComponent(self):
        return self.getDisplayComponent("sidebar")
