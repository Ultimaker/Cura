# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os.path
from UM.Application import Application
from UM.PluginRegistry import PluginRegistry
from cura.Stages.CuraStage import CuraStage


class PrepareStage(CuraStage):
    """Stage for preparing model (slicing)."""

    def __init__(self, parent = None):
        super().__init__(parent)
        Application.getInstance().engineCreatedSignal.connect(self._engineCreated)

    def _engineCreated(self):
        menu_component_path = os.path.join(PluginRegistry.getInstance().getPluginPath("PrepareStage"), "PrepareMenu.qml")
        main_component_path = os.path.join(PluginRegistry.getInstance().getPluginPath("PrepareStage"), "PrepareMain.qml")
        self.addDisplayComponent("menu", menu_component_path)
        self.addDisplayComponent("main", main_component_path)