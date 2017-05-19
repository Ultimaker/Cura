# Copyright (c) 2017 Tim Kuipers
# Cura is released under the terms of the AGPLv3 or higher.

import os.path

from UM.Application import Application
from UM.Math.Color import Color
from UM.PluginRegistry import PluginRegistry
from UM.Event import Event
from UM.View.View import View
from UM.View.RenderBatch import RenderBatch
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator

from UM.View.RenderBatch import RenderBatch
from UM.View.GL.OpenGL import OpenGL


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

        for node in BreadthFirstIterator(scene.getRoot()):
            if not node.render(renderer):
                if node.getMeshData() and node.isVisible():
                    renderer.queueNode(node,
                                       shader = self._wireframe_shader,
                                       type = RenderBatch.RenderType.Solid,
                                       blend_mode = RenderBatch.BlendMode.Additive,
                                       sort = -10,
                                       state_setup_callback = lambda gl: gl.glDepthFunc(gl.GL_ALWAYS),
                                       state_teardown_callback = lambda gl: gl.glDepthFunc(gl.GL_LESS)
                    )

    def endRendering(self):
        pass
