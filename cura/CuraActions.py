# Copyright (c) 2023 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.
from typing import List, cast

from PyQt6.QtCore import QObject, QUrl, pyqtSignal, pyqtProperty
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QApplication

from UM.Application import Application
from UM.Event import CallFunctionEvent
from UM.FlameProfiler import pyqtSlot
from UM.Math.Vector import Vector
from UM.Scene.Selection import Selection
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
from UM.Operations.TranslateOperation import TranslateOperation

import cura.CuraApplication
from cura.Operations.SetParentOperation import SetParentOperation
from cura.MultiplyObjectsJob import MultiplyObjectsJob
from cura.Settings.SetObjectExtruderOperation import SetObjectExtruderOperation
from cura.Settings.ExtruderManager import ExtruderManager

from cura.Arranging.GridArrange import GridArrange
from cura.Arranging.Nest2DArrange import Nest2DArrange


from cura.Operations.SetBuildPlateNumberOperation import SetBuildPlateNumberOperation

from UM.Logger import Logger
from UM.Scene.SceneNode import SceneNode

class CuraActions(QObject):
    def __init__(self, parent: QObject = None) -> None:
        super().__init__(parent)

        self._operation_stack = Application.getInstance().getOperationStack()
        self._operation_stack.changed.connect(self._onUndoStackChanged)

    undoStackChanged = pyqtSignal()
    @pyqtSlot()
    def openDocumentation(self) -> None:
        # Starting a web browser from a signal handler connected to a menu will crash on windows.
        # So instead, defer the call to the next run of the event loop, since that does work.
        # Note that weirdly enough, only signal handlers that open a web browser fail like that.
        event = CallFunctionEvent(self._openUrl, [QUrl("https://ultimaker.com/en/resources/manuals/software?utm_source=cura&utm_medium=software&utm_campaign=dropdown-documentation")], {})
        cura.CuraApplication.CuraApplication.getInstance().functionEvent(event)

    @pyqtProperty(bool, notify=undoStackChanged)
    def canUndo(self):
        return self._operation_stack.canUndo()

    @pyqtProperty(bool, notify=undoStackChanged)
    def canRedo(self):
        return self._operation_stack.canRedo()

    @pyqtSlot()
    def undo(self):
        self._operation_stack.undo()

    @pyqtSlot()
    def redo(self):
        self._operation_stack.redo()

    def _onUndoStackChanged(self):
        self.undoStackChanged.emit()

    @pyqtSlot()
    def openBugReportPage(self) -> None:
        event = CallFunctionEvent(self._openUrl, [QUrl("https://github.com/Ultimaker/Cura/issues/new/choose")], {})
        cura.CuraApplication.CuraApplication.getInstance().functionEvent(event)

    @pyqtSlot()
    def homeCamera(self) -> None:
        """Reset camera position and direction to default"""

        scene = cura.CuraApplication.CuraApplication.getInstance().getController().getScene()
        camera = scene.getActiveCamera()
        if camera:
            diagonal_size = cura.CuraApplication.CuraApplication.getInstance().getBuildVolume().getDiagonalSize()
            camera.setPosition(Vector(-80, 250, 700) * diagonal_size / 375)
            camera.setPerspective(True)
            camera.lookAt(Vector(0, 0, 0))

    @pyqtSlot()
    def centerSelection(self) -> None:
        """Center all objects in the selection"""

        operation = GroupedOperation()
        for node in Selection.getAllSelectedObjects():
            current_node = node
            parent_node = current_node.getParent()
            while parent_node and parent_node.callDecoration("isGroup"):
                current_node = parent_node
                parent_node = current_node.getParent()

            # Find out where the bottom of the object is
            bbox = current_node.getBoundingBox()
            if bbox:
                center_y = current_node.getWorldPosition().y - bbox.bottom
            else:
                center_y = 0

            # Move the object so that it's bottom is on to of the buildplate
            center_operation = TranslateOperation(current_node, Vector(0, center_y, 0), set_position = True)
            operation.addOperation(center_operation)
        operation.push()
    @pyqtSlot(int)
    def multiplySelection(self, count: int) -> None:
        """Multiply all objects in the selection
        :param count: The number of times to multiply the selection.
        """
        min_offset = cura.CuraApplication.CuraApplication.getInstance().getBuildVolume().getEdgeDisallowedSize() + 2  # Allow for some rounding errors
        job = MultiplyObjectsJob(Selection.getAllSelectedObjects(), count, min_offset = max(min_offset, 8))
        job.start()

    @pyqtSlot(int)
    def multiplySelectionToGrid(self, count: int) -> None:
        """Multiply all objects in the selection

        :param count: The number of times to multiply the selection.
        """

        min_offset = cura.CuraApplication.CuraApplication.getInstance().getBuildVolume().getEdgeDisallowedSize() + 2  # Allow for some rounding errors
        job = MultiplyObjectsJob(Selection.getAllSelectedObjects(), count, min_offset=max(min_offset, 8),
                                 grid_arrange=True)
        job.start()

    @pyqtSlot()
    def deleteSelection(self) -> None:
        """Delete all selected objects."""

        if not cura.CuraApplication.CuraApplication.getInstance().getController().getToolsEnabled():
            return

        removed_group_nodes = [] #type: List[SceneNode]
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

            # Reset the print information
            cura.CuraApplication.CuraApplication.getInstance().getController().getScene().sceneChanged.emit(node)

        op.push()

    @pyqtSlot(str)
    def setExtruderForSelection(self, extruder_id: str) -> None:
        """Set the extruder that should be used to print the selection.

        :param extruder_id: The ID of the extruder stack to use for the selected objects.
        """

        operation = GroupedOperation()

        nodes_to_change = []
        for node in Selection.getAllSelectedObjects():
            # If the node is a group, apply the active extruder to all children of the group.
            if node.callDecoration("isGroup"):
                for grouped_node in BreadthFirstIterator(node): #type: ignore #Ignore type error because iter() should get called automatically by Python syntax.
                    if grouped_node.callDecoration("getActiveExtruder") == extruder_id:
                        continue

                    if grouped_node.callDecoration("isGroup"):
                        continue

                    nodes_to_change.append(grouped_node)
                continue

            # Do not change any nodes that already have the right extruder set.
            if node.callDecoration("getActiveExtruder") == extruder_id:
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

    @pyqtSlot(int)
    def setBuildPlateForSelection(self, build_plate_nr: int) -> None:
        Logger.log("d", "Setting build plate number... %d" % build_plate_nr)
        operation = GroupedOperation()

        root = cura.CuraApplication.CuraApplication.getInstance().getController().getScene().getRoot()

        nodes_to_change = []  # type: List[SceneNode]
        for node in Selection.getAllSelectedObjects():
            parent_node = node  # Find the parent node to change instead
            while parent_node.getParent() != root:
                parent_node = cast(SceneNode, parent_node.getParent())

            for single_node in BreadthFirstIterator(parent_node):  # type: ignore #Ignore type error because iter() should get called automatically by Python syntax.
                nodes_to_change.append(single_node)

        if not nodes_to_change:
            Logger.log("d", "Nothing to change.")
            return

        for node in nodes_to_change:
            operation.addOperation(SetBuildPlateNumberOperation(node, build_plate_nr))
        operation.push()

        Selection.clear()

    @pyqtSlot()
    def cut(self) -> None:
        self.copy()
        self.deleteSelection()

    @pyqtSlot()
    def copy(self) -> None:
        mesh_writer = cura.CuraApplication.CuraApplication.getInstance().getMeshFileHandler().getWriter("3MFWriter")
        if not mesh_writer:
            Logger.log("e", "No 3MF writer found, unable to copy.")
            return

        # Get the selected nodes
        selected_objects = Selection.getAllSelectedObjects()
        # Serialize the nodes to a string
        scene_string = mesh_writer.sceneNodesToString(selected_objects)
        # Put the string on the clipboard
        QApplication.clipboard().setText(scene_string)

    @pyqtSlot()
    def paste(self) -> None:
        application = cura.CuraApplication.CuraApplication.getInstance()
        mesh_reader = application.getMeshFileHandler().getReaderForFile(".3mf")
        if not mesh_reader:
            Logger.log("e", "No 3MF reader found, unable to paste.")
            return

        # Parse the scene from the clipboard
        scene_string = QApplication.clipboard().text()

        nodes = mesh_reader.stringToSceneNodes(scene_string)

        if not nodes:
            # Nothing to paste
            return

        # Find all fixed nodes, these are the nodes that should be avoided when arranging
        fixed_nodes = []
        root = application.getController().getScene().getRoot()
        for node in DepthFirstIterator(root):
            # Only count sliceable objects
            if node.callDecoration("isSliceable"):
                fixed_nodes.append(node)
        # Add the new nodes to the scene, and arrange them

        arranger = GridArrange(nodes, application.getBuildVolume(), fixed_nodes)
        group_operation, not_fit_count = arranger.createGroupOperationForArrange(add_new_nodes_in_scene = True)
        group_operation.push()

        # deselect currently selected nodes, and select the new nodes
        for node in Selection.getAllSelectedObjects():
            Selection.remove(node)

        numberOfFixedNodes = len(fixed_nodes)
        for node in nodes:
            numberOfFixedNodes += 1
            node.printOrder = numberOfFixedNodes
            Selection.add(node)

    def _openUrl(self, url: QUrl) -> None:
        QDesktopServices.openUrl(url)
