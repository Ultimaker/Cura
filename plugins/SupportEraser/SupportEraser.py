# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from UM.Math.Vector import Vector
from UM.Tool import Tool
from PyQt5.QtCore import Qt, QUrl
from UM.Application import Application
from UM.Event import Event, MouseEvent
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Settings.SettingInstance import SettingInstance
from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator
from cura.Scene.BuildPlateDecorator import BuildPlateDecorator
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator
from cura.Settings.SettingOverrideDecorator import SettingOverrideDecorator
from cura.DepthPass import DepthPass

import os
import os.path

class SupportEraser(Tool):
    def __init__(self):
        super().__init__()
        self._shortcut_key = Qt.Key_G
        self._controller = Application.getInstance().getController()

    def event(self, event):
        super().event(event)

        if event.type == Event.MousePressEvent and self._controller.getToolsEnabled():
            active_camera = self._controller.getScene().getActiveCamera()

            # Create depth pass for picking
            render_width, render_height = active_camera.getWindowSize()
            depth_pass = DepthPass(int(render_width), int(render_height))
            depth_pass.render()

            distance = depth_pass.getDepthAtPosition(event.x, event.y)
            ray = active_camera.getRay(event.x, event.y)
            picked_position = ray.getPointAlongRay(distance)

            # Add the anto_overhang_mesh cube:
            self._createEraserMesh(picked_position)

    def _createEraserMesh(self, position: Vector):
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
