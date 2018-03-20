# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QTimer
from cura.Scene.CuraSceneNode import CuraSceneNode

from UM.Application import Application
from UM.Tool import Tool
from UM.Message import Message
from UM.i18n import i18nCatalog
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator

catalog = i18nCatalog("cura")


SHRINKAGE_THRESHOLD = 0.5
WARNING_SIZE_XY = 150
WARNING_SIZE_Z = 100


class ModelChecker(Tool):
    def __init__(self):
        super().__init__()

        self._last_known_tool_id = None

        self._controller.activeToolChanged.connect(self._onActiveToolChanged)

    def checkObjects(self, nodes_to_check):
        warning_nodes = []
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack is None:
            return []
        material_shrinkage = {}
        need_check = False

        # Get all shrinkage values of materials used
        for extruder_position, extruder in global_container_stack.extruders.items():
            shrinkage = extruder.material.getProperty("material_shrinkage_ratio_percentage", "value")
            if shrinkage is None:
                shrinkage = 0
            if shrinkage > SHRINKAGE_THRESHOLD:
                need_check = True
            material_shrinkage[extruder_position] = shrinkage

        # Check if we can bail out fast
        if not need_check:
            return

        # Check node material shrinkage and bounding box size
        for node in nodes_to_check:
            node_extruder_position = node.callDecoration("getActiveExtruderPosition")
            if material_shrinkage[node_extruder_position] > SHRINKAGE_THRESHOLD:
                bbox = node.getBoundingBox()
                if bbox.width >= WARNING_SIZE_XY or bbox.depth >= WARNING_SIZE_XY or bbox.height >= WARNING_SIZE_Z:
                    warning_nodes.append(node)

        return warning_nodes

    def checkAllSliceableNodes(self):
        # Add all sliceable scene nodes to check
        scene = Application.getInstance().getController().getScene()
        nodes_to_check = []
        for node in DepthFirstIterator(scene.getRoot()):
            if node.callDecoration("isSliceable"):
                nodes_to_check.append(node)
        return self.checkObjects(nodes_to_check)

    ##  Display warning message
    def showWarningMessage(self, warning_nodes):
        caution_message = Message(catalog.i18nc(
            "@info:status",
            "Some models may not be printed optimal due to object size and material chosen [%s].\n"
            "Tips that may be useful to improve the print quality:\n"
            "1) Use rounded corners\n"
            "2) Turn the fan off (only if the are no tiny details on the model)\n"
            "3) Use a different material") % ", ".join([n.getName() for n in warning_nodes]),
            lifetime = 0,
            title = catalog.i18nc("@info:title", "Model Checker Warning"))
        caution_message.show()

    def showHappyMessage(self):
        happy_message = Message(catalog.i18nc(
            "@info:status",
            "The Model Checker did not detect any problems with your model / print setup combination."),
            lifetime = 5,
            title = catalog.i18nc("@info:title", "Model Checker"))
        happy_message.show()

    def _onActiveToolChanged(self):
        active_tool = self.getController().getActiveTool()
        if active_tool is None:
            return
        active_tool_id = active_tool.getPluginId()
        if active_tool_id != self.getPluginId():
            self._last_known_tool_id = active_tool_id
        if active_tool_id == self.getPluginId():
            warning_nodes = self.checkAllSliceableNodes()
            if warning_nodes:
                self.showWarningMessage(warning_nodes)
            else:
                self.showHappyMessage()
            if self._last_known_tool_id is not None:
                self.getController().setActiveTool(self._last_known_tool_id)
