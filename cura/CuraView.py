# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty, QUrl

from UM.View.View import View


# Since Cura has a few pre-defined "space claims" for the locations of certain components, we've provided some structure
# to indicate this.
#   MainComponent works in the same way the MainComponent of a stage.
#   the stageMenuComponent returns an item that should be used somehwere in the stage menu. It's up to the active stage
#   to actually do something with this.
class CuraView(View):
    def __init__(self, parent = None) -> None:
        super().__init__(parent)

    @pyqtProperty(QUrl, constant = True)
    def mainComponent(self) -> QUrl:
        return self.getDisplayComponent("main")

    @pyqtProperty(QUrl, constant = True)
    def stageMenuComponent(self) -> QUrl:
        return self.getDisplayComponent("menu")