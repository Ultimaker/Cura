# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import os.path

from UM.Application import Application
from cura.Stages.CuraStage import CuraStage

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from UM.View import View

class PreviewStage(CuraStage):
    def __init__(self, application: Application, parent = None) -> None:
        super().__init__(parent)
        self._application = application
        self._application.engineCreatedSignal.connect(self._engineCreated)
        self._previously_active_view = None  # type: Optional[View]

    def onStageSelected(self) -> None:
        self._previously_active_view = self._application.getController().getActiveView()

    def onStageDeselected(self) -> None:
        if self._previously_active_view is not None:
            self._application.getController().setActiveView(self._previously_active_view.getPluginId())
        self._previously_active_view = None

    def _engineCreated(self) -> None:
        menu_component_path = os.path.join(self._application.getPluginRegistry().getPluginPath(self.getPluginId()),
                                           "PreviewMenu.qml")
        self.addDisplayComponent("menu", menu_component_path)
