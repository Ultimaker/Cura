# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty, QUrl

from UM.Stage import Stage


# Since Cura has a few pre-defined "space claims" for the locations of certain components, we've provided some structure
# to indicate this.
# * The StageMenuComponent is the horizontal area below the stage bar. This should be used to show stage specific
#   buttons and elements. This component will be drawn over the bar & main component.
# * The MainComponent is the component that will be drawn starting from the bottom of the stageBar and fills the rest
#   of the screen.
class CuraStage(Stage):
    def __init__(self, parent = None) -> None:
        super().__init__(parent)

    @pyqtProperty(str, constant = True)
    def stageId(self) -> str:
        return self.getPluginId()

    @pyqtProperty(QUrl, constant = True)
    def mainComponent(self) -> QUrl:
        return self.getDisplayComponent("main")

    @pyqtProperty(QUrl, constant = True)
    def stageMenuComponent(self) -> QUrl:
        return self.getDisplayComponent("menu")