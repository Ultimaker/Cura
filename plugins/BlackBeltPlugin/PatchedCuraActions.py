from UM.FlameProfiler import pyqtSlot
from UM.Scene.Selection import Selection

from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation

import cura.CuraApplication
from cura.CuraActions import CuraActions
from cura.MultiplyObjectsJob import MultiplyObjectsJob

import copy

class PatchedCuraActions(CuraActions):
    ##  Multiply all objects in the selection
    #
    #   \param count The number of times to multiply the selection.
    @pyqtSlot(int)
    def multiplySelection(self, count: int) -> None:
        application = cura.CuraApplication.CuraApplication.getInstance()
        global_container_stack = application.getGlobalContainerStack()

        if not global_container_stack:
            return

        definition_container = global_container_stack.getBottom()
        if definition_container.getId() != "blackbelt":
            # for all other printers do the normal multiply/arrange
            super().multiplySelection(count)
            return

        scene_root = application.getController().getScene().getRoot()

        current_nodes = []
        for node in DepthFirstIterator(scene_root):
            if node.callDecoration("isSliceable") or node.callDecoration("isGroup"):
                current_nodes.append(node)

        new_nodes = []
        processed_nodes = []

        active_build_plate = application.getMultiBuildPlateModel().activeBuildPlate

        for node in Selection.getAllSelectedObjects()[:]:
            # If object is part of a group, multiply group
            while node.getParent() and (node.getParent().callDecoration("isGroup") or node.getParent().callDecoration("isSliceable")):
                node = node.getParent()

            if node in processed_nodes:
                continue
            processed_nodes.append(node)

            for i in range(count):
                new_node = copy.deepcopy(node)

                new_node.callDecoration("setBuildPlateNumber", active_build_plate)
                for child in new_node.getChildren():
                    child.callDecoration("setBuildPlateNumber", active_build_plate)

                new_nodes.append(new_node)

        if new_nodes:
            op = GroupedOperation()
            for new_node in new_nodes:
                op.addOperation(AddSceneNodeOperation(new_node, scene_root))
            op.push()

        application.arrange(new_nodes, current_nodes)