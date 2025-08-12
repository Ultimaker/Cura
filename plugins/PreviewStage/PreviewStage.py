# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os.path

from UM.Qt.QtApplication import QtApplication
from cura.Stages.CuraStage import CuraStage

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from UM.View.View import View


class PreviewStage(CuraStage):
    """Displays a preview of what you're about to print.

    The Python component of this stage just loads PreviewMain.qml for display
    when the stage is selected, and makes sure that it reverts to the previous
    view when the previous stage is activated.
    """

    def __init__(self, application: QtApplication, parent = None) -> None:
        super().__init__(parent)
        self._application = application
        self._application.engineCreatedSignal.connect(self._engineCreated)

    def _engineCreated(self) -> None:
        """Delayed load of the QML files.

        We need to make sure that the QML engine is running before we can load
        these.
        """

        plugin_path = self._application.getPluginRegistry().getPluginPath(self.getPluginId())
        if plugin_path is not None:
            menu_component_path = os.path.join(plugin_path, "PreviewMenu.qml")
            main_component_path = os.path.join(plugin_path, "PreviewMain.qml")
            self.addDisplayComponent("menu", menu_component_path)
            self.addDisplayComponent("main", main_component_path)
