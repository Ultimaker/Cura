# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import QObject, QUrl
from PyQt5.QtGui import QDesktopServices
from UM.FlameProfiler import pyqtSlot

from UM.Event import CallFunctionEvent
from UM.Application import Application
from UM.Math.Vector import Vector
from UM.Scene.Selection import Selection
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
from UM.Operations.SetTransformOperation import SetTransformOperation

from cura.SetParentOperation import SetParentOperation
from cura.MultiplyObjectsJob import MultiplyObjectsJob
from cura.Settings.SetObjectExtruderOperation import SetObjectExtruderOperation
from cura.Settings.ExtruderManager import ExtruderManager

class CuraActions(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)

    @pyqtSlot()
    def openDocumentation(self):
        # Starting a web browser from a signal handler connected to a menu will crash on windows.
        # So instead, defer the call to the next run of the event loop, since that does work.
        # Note that weirdly enough, only signal handlers that open a web browser fail like that.
        event = CallFunctionEvent(self._openUrl, [QUrl("http://ultimaker.com/en/support/software")], {})
        Application.getInstance().functionEvent(event)

    @pyqtSlot()
    def openBugReportPage(self):
        event = CallFunctionEvent(self._openUrl, [QUrl("http://github.com/Ultimaker/Cura/issues")], {})
        Application.getInstance().functionEvent(event)

    ##  Reset camera position and direction to default
    @pyqtSlot()
    def homeCamera(self) -> None:
        scene = Application.getInstance().getController().getScene()
        camera = scene.getActiveCamera()
        camera.setPosition(Vector(-80, 250, 700))
        camera.setPerspective(True)
        camera.lookAt(Vector(0, 0, 0))

    ##  Center all objects in the selection
    @pyqtSlot()
    def centerSelection(self) -> None:
        operation = GroupedOperation()
        for node in Selection.getAllSelectedObjects():
            current_node = node
            while current_node.getParent() and current_node.getParent().callDecoration("isGroup"):
                current_node = current_node.getParent()

            center_operation = SetTransformOperation(current_node, Vector())
            operation.addOperation(center_operation)
        operation.push()

    ##  Multiply all objects in the selection
    #
    #   \param count The number of times to multiply the selection.
    @pyqtSlot(int)
    def multiplySelection(self, count: int) -> None:
        job = MultiplyObjectsJob(Selection.getAllSelectedObjects(), count, 8)
        job.start()

    ##  Delete all selected objects.
    @pyqtSlot()
    def deleteSelection(self) -> None:
        if not Application.getInstance().getController().getToolsEnabled():
            return

        removed_group_nodes = []
        op = GroupedOperation()
        nodes = Selection.getAllSelectedObjects()
        for node in nodes:
            op.addOperation(RemoveSceneNodeOperation(node))
            group_node = node.getParent()
            if group_node and group_node.callDecoration("isGroup") and group_node not in removed_group_nodes:
                remaining_nodes_in_group = list(set(group_node.getChildren()) - set(nodes))
                if len(remaining_nodes_in_group) == 1:
                    removed_group_nodes.append(group_node)
                    op.addOperation(SetParentOperation(remaining_nodes_in_group[0], group_node.getParent()))
                    op.addOperation(RemoveSceneNodeOperation(group_node))
        op.push()

    ##  Set the extruder that should be used to print the selection.
    #
    #   \param extruder_id The ID of the extruder stack to use for the selected objects.
    @pyqtSlot(str)
    def setExtruderForSelection(self, extruder_id: str) -> None:
        operation = GroupedOperation()

        nodes_to_change = []
        for node in Selection.getAllSelectedObjects():
            # Do not change any nodes that already have the right extruder set.
            if node.callDecoration("getActiveExtruder") == extruder_id:
                continue

            # If the node is a group, apply the active extruder to all children of the group.
            if node.callDecoration("isGroup"):
                for grouped_node in BreadthFirstIterator(node):
                    if grouped_node.callDecoration("getActiveExtruder") == extruder_id:
                        continue

                    if grouped_node.callDecoration("isGroup"):
                        continue

                    nodes_to_change.append(grouped_node)
                continue

            nodes_to_change.append(node)

        if not nodes_to_change:
            # If there are no changes to make, we still need to reset the selected extruders.
            # This is a workaround for checked menu items being deselected while still being
            # selected.
            ExtruderManager.getInstance().resetSelectedObjectExtruders()
            return

        for node in nodes_to_change:
            operation.addOperation(SetObjectExtruderOperation(node, extruder_id))
        operation.push()

    def _openUrl(self, url):
        QDesktopServices.openUrl(url)
