# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty, QUrl
from typing import Optional, TYPE_CHECKING

from UM.Resources import Resources
from UM.View.View import View

from cura.CuraApplication import CuraApplication

if TYPE_CHECKING:
    from PyQt5.QtCore import QObject

# Since Cura has a few pre-defined "space claims" for the locations of certain components, we've provided some structure
# to indicate this.
#   MainComponent works in the same way the MainComponent of a stage.
#   the stageMenuComponent returns an item that should be used somewhere in the stage menu. It's up to the active stage
#   to actually do something with this.
class CuraView(View):
    def __init__(self, parent: Optional["QObject"] = None, use_empty_menu_placeholder: bool = False) -> None:
        super().__init__(parent)

        self._empty_menu_placeholder_url = QUrl.fromLocalFile(Resources.getPath(CuraApplication.ResourceTypes.QmlFiles,
                                                                                "EmptyViewMenuComponent.qml"))
        self._use_empty_menu_placeholder = use_empty_menu_placeholder

    @pyqtProperty(QUrl, constant = True)
    def mainComponent(self) -> QUrl:
        return self.getDisplayComponent("main")


    @pyqtProperty(QUrl, constant = True)
    def stageMenuComponent(self) -> QUrl:
        url = self.getDisplayComponent("menu")
        if not url.toString() and self._use_empty_menu_placeholder:
            url = self._empty_menu_placeholder_url
        return url
