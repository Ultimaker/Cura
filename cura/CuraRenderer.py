# Copyright (c) 2025 UltiMaker
# Uranium is released under the terms of the LGPLv3 or higher.


from typing import TYPE_CHECKING

from cura.PickingPass import PickingPass
from UM.Qt.QtRenderer import QtRenderer
from UM.View.RenderPass import RenderPass
from UM.View.SelectionPass import SelectionPass

if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication


class CuraRenderer(QtRenderer):
    """An overridden Renderer implementation that adds some behaviors specific to Cura."""

    def __init__(self, application: "CuraApplication") -> None:
        super().__init__()

        self._controller = application.getController()
        self._controller.activeToolChanged.connect(self._onActiveToolChanged)
        self._extra_rendering_passes: list[RenderPass] = []

    def _onActiveToolChanged(self) -> None:
        tool_extra_rendering_passes = []

        active_tool = self._controller.getActiveTool()
        if active_tool is not None:
            tool_extra_rendering_passes = active_tool.getRequiredExtraRenderingPasses()

        for extra_rendering_pass in self._extra_rendering_passes:
            extra_rendering_pass.setEnabled(extra_rendering_pass.getName() in tool_extra_rendering_passes)

    def _makeRenderPasses(self) -> list[RenderPass]:
        self._extra_rendering_passes = [
            SelectionPass(self._viewport_width, self._viewport_height, SelectionPass.SelectionMode.FACES),
            PickingPass(self._viewport_width, self._viewport_height, only_selected_objects=True),
            PickingPass(self._viewport_width, self._viewport_height, only_selected_objects=False)
        ]

        for extra_rendering_pass in self._extra_rendering_passes:
            extra_rendering_pass.setEnabled(False)

        return super()._makeRenderPasses() + self._extra_rendering_passes
