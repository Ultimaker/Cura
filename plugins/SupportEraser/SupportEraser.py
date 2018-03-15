# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os
import os.path

from PyQt5.QtCore import Qt, QUrl

from UM.Math.Vector import Vector
from UM.Tool import Tool
from UM.Application import Application
from UM.Event import Event, MouseEvent

from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Scene.Selection import Selection
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator
from cura.Scene.CuraSceneNode import CuraSceneNode

from cura.PickingPass import PickingPass

from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
from cura.Operations.SetParentOperation import SetParentOperation

from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator
from cura.Scene.BuildPlateDecorator import BuildPlateDecorator
from UM.Scene.GroupDecorator import GroupDecorator
from cura.Settings.SettingOverrideDecorator import SettingOverrideDecorator

from UM.Settings.SettingInstance import SettingInstance

class SupportEraser(Tool):
    def __init__(self):
        super().__init__()
        self._shortcut_key = Qt.Key_G
        self._controller = Application.getInstance().getController()

        self._selection_pass = None
        Application.getInstance().globalContainerStackChanged.connect(self._updateEnabled)

    def event(self, event):
        super().event(event)

        if event.type == Event.MousePressEvent and self._controller.getToolsEnabled():

            if self._selection_pass is None:
                # The selection renderpass is used to identify objects in the current view
                self._selection_pass = Application.getInstance().getRenderer().getRenderPass("selection")
            picked_node = self._controller.getScene().findObject(self._selection_pass.getIdAtPosition(event.x, event.y))

            node_stack = picked_node.callDecoration("getStack")
            if node_stack:
                if node_stack.getProperty("anti_overhang_mesh", "value"):
                    self._removeEraserMesh(picked_node)
                    return

                elif node_stack.getProperty("support_mesh", "value") or node_stack.getProperty("infill_mesh", "value") or node_stack.getProperty("cutting_mesh", "value"):
                    # Only "normal" meshes can have anti_overhang_meshes added to them
                    return

            # Create a pass for picking a world-space location from the mouse location
            active_camera = self._controller.getScene().getActiveCamera()
            picking_pass = PickingPass(active_camera.getViewportWidth(), active_camera.getViewportHeight())
            picking_pass.render()

            picked_position = picking_pass.getPickedPosition(event.x, event.y)

            # Add the anti_overhang_mesh cube at the picked location
            self._createEraserMesh(picked_node, picked_position)

    def _createEraserMesh(self, parent: CuraSceneNode, position: Vector):
        node = CuraSceneNode()

        node.setName("Eraser")
        node.setSelectable(True)
        mesh = MeshBuilder()
        mesh.addCube(10,10,10)
        node.setMeshData(mesh.build())
        node.setPosition(position)

        active_build_plate = Application.getInstance().getMultiBuildPlateModel().activeBuildPlate

        node.addDecorator(SettingOverrideDecorator())
        node.addDecorator(BuildPlateDecorator(active_build_plate))
        node.addDecorator(SliceableObjectDecorator())

        stack = node.callDecoration("getStack") # created by SettingOverrideDecorator
        settings = stack.getTop()

        definition = stack.getSettingDefinition("anti_overhang_mesh")
        new_instance = SettingInstance(definition, settings)
        new_instance.setProperty("value", True)
        new_instance.resetState()  # Ensure that the state is not seen as a user state.
        settings.addInstance(new_instance)

        root = self._controller.getScene().getRoot()

        op = GroupedOperation()
        # First add the node to the scene, so it gets the expected transform
        op.addOperation(AddSceneNodeOperation(node, root))

        # Determine the parent group the node should be put in
        if parent.getParent().callDecoration("isGroup"):
            group = parent.getParent()
        else:
            # Create a group-node
            group = CuraSceneNode()
            group.addDecorator(GroupDecorator())
            group.addDecorator(BuildPlateDecorator(active_build_plate))
            group.setParent(root)
            center = parent.getPosition()
            group.setPosition(center)
            group.setCenterPosition(center)
            op.addOperation(SetParentOperation(parent, group))

        op.addOperation(SetParentOperation(node, group))
        op.push()
        Application.getInstance().getController().getScene().sceneChanged.emit(node)

        # Select the picked node so the group does not get drawn as a wireframe (yet)
        if Selection.isSelected(group):
            Selection.remove(group)
        if not Selection.isSelected(parent):
            Selection.add(parent)

    def _removeEraserMesh(self, node: CuraSceneNode):
        group = node.getParent()
        if group.callDecoration("isGroup"):
            parent = group.getChildren()[0]

        op = GroupedOperation()
        op.addOperation(RemoveSceneNodeOperation(node))
        if len(group.getChildren()) == 2:
            op.addOperation(SetParentOperation(parent, group.getParent()))

        op.push()
        Application.getInstance().getController().getScene().sceneChanged.emit(node)

        # Select the picked node so the group does not get drawn as a wireframe (yet)
        if Selection.isSelected(group):
            Selection.remove(group)
        if parent and not Selection.isSelected(parent):
            Selection.add(parent)

    def _updateEnabled(self):
        plugin_enabled = False

        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            plugin_enabled = global_container_stack.getProperty("anti_overhang_mesh", "enabled")

        Application.getInstance().getController().toolEnabledChanged.emit(self._plugin_id, plugin_enabled)
