# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from UM.Math.Vector import Vector
from UM.Tool import Tool
from PyQt5.QtCore import Qt, QUrl
from UM.Application import Application
from UM.Event import Event, MouseEvent
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
from UM.Settings.SettingInstance import SettingInstance
from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator
from cura.Scene.BuildPlateDecorator import BuildPlateDecorator
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator
from cura.Settings.SettingOverrideDecorator import SettingOverrideDecorator
from cura.PickingPass import PickingPass

import os
import os.path

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

        stack = node.callDecoration("getStack") #Don't try to get the active extruder since it may be None anyway.
        if not stack:
            node.addDecorator(SettingOverrideDecorator())
            stack = node.callDecoration("getStack")

        settings = stack.getTop()

        if not (settings.getInstance("anti_overhang_mesh") and settings.getProperty("anti_overhang_mesh", "value")):
            definition = stack.getSettingDefinition("anti_overhang_mesh")
            new_instance = SettingInstance(definition, settings)
            new_instance.setProperty("value", True)
            new_instance.resetState()  # Ensure that the state is not seen as a user state.
            settings.addInstance(new_instance)

        scene = self._controller.getScene()
        op = AddSceneNodeOperation(node, scene.getRoot())
        op.push()
        Application.getInstance().getController().getScene().sceneChanged.emit(node)

    def _removeEraserMesh(self, node: CuraSceneNode):
        op = RemoveSceneNodeOperation(node)
        op.push()
        Application.getInstance().getController().getScene().sceneChanged.emit(node)

    def _updateEnabled(self):
        plugin_enabled = False

        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            plugin_enabled = global_container_stack.getProperty("anti_overhang_mesh", "enabled")

        Application.getInstance().getController().toolEnabledChanged.emit(self._plugin_id, plugin_enabled)
