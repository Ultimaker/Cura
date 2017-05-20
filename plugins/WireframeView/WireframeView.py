# Copyright (c) 2017 Tim Kuipers
# Cura is released under the terms of the AGPLv3 or higher.

import os.path

from UM.Application import Application
from UM.Math.Color import Color
from UM.PluginRegistry import PluginRegistry
from UM.Preferences import Preferences
from UM.Event import Event
from UM.View.View import View
from UM.View.RenderBatch import RenderBatch
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator

from UM.View.RenderBatch import RenderBatch
from UM.View.GL.OpenGL import OpenGL

from UM.Settings.Validator import ValidatorState
from cura.Settings.ExtruderManager import ExtruderManager
from cura.Settings.ExtrudersModel import ExtrudersModel

import math


## View used to display the edges of objects.
class WireframeView(View):
    def __init__(self):
        super().__init__()

        self._wireframe_shader = None

    def beginRendering(self):
        scene = self.getController().getScene()
        renderer = self.getRenderer()

        if not self._wireframe_shader:
            self._wireframe_shader = OpenGL.getInstance().createShaderProgram(os.path.join(PluginRegistry.getInstance().getPluginPath("WireframeView"), "wireframe.shader"))
            self._wireframe_shader.setUniformValue("u_color", Color(*Application.getInstance().getTheme().getColor("xray").getRgb()))
            self._wireframe_shader.setUniformValue("u_color_error", Color(*Application.getInstance().getTheme().getColor("xray_error").getRgb()))

        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            multi_extrusion = global_container_stack.getProperty("machine_extruder_count", "value") > 1

            if multi_extrusion:
                support_extruder_nr = global_container_stack.getProperty("support_extruder_nr", "value")
                support_angle_stack = ExtruderManager.getInstance().getExtruderStack(support_extruder_nr)
                if not support_angle_stack:
                    support_angle_stack = global_container_stack
            else:
                support_angle_stack = global_container_stack
            if Preferences.getInstance().getValue("view/show_overhang"):
                angle = support_angle_stack.getProperty("support_angle", "value")
                # Make sure the overhang angle is valid before passing it to the shader
                # Note: if the overhang angle is set to its default value, it does not need to get validated (validationState = None)
                if angle is not None and global_container_stack.getProperty("support_angle", "validationState") in [None, ValidatorState.Valid]:
                    self._wireframe_shader.setUniformValue("u_overhangAngle", math.cos(math.radians(90 - angle)))
                else:
                    self._wireframe_shader.setUniformValue("u_overhangAngle", math.cos(math.radians(0))) #Overhang angle of 0 causes no area at all to be marked as overhang.
            else:
                self._wireframe_shader.setUniformValue("u_overhangAngle", math.cos(math.radians(0)))
                    

        for node in BreadthFirstIterator(scene.getRoot()):
            if not node.render(renderer):
                if node.getMeshData() and node.isVisible():
                    renderer.queueNode(node,
                                       shader = self._wireframe_shader,
                                       type = RenderBatch.RenderType.Solid,
                                       blend_mode = RenderBatch.BlendMode.Additive,
                                       sort = -10,
                                       state_setup_callback = lambda gl: gl.glDepthFunc(gl.GL_ALWAYS),
                                       state_teardown_callback = lambda gl: gl.glDepthFunc(gl.GL_LESS),
                                       mode = RenderBatch.RenderMode.TrianglesAdjacency
                    )

    def endRendering(self):
        pass
