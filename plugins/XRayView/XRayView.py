# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os.path
from PyQt5.QtGui import QOpenGLContext

from UM.Application import Application
from UM.Logger import Logger
from UM.Math.Color import Color
from UM.PluginRegistry import PluginRegistry
from UM.Resources import Resources
from UM.Platform import Platform
from UM.Event import Event
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator

from UM.View.RenderBatch import RenderBatch
from UM.View.GL.OpenGL import OpenGL

from cura.CuraApplication import CuraApplication
from cura.CuraView import CuraView
from cura.Scene.ConvexHullNode import ConvexHullNode

from cura import XRayPass


## View used to display a see-through version of objects with errors highlighted.
class XRayView(CuraView):
    def __init__(self):
        super().__init__(parent = None, use_empty_menu_placeholder = True)

        self._xray_shader = None
        self._xray_pass = None
        self._xray_composite_shader = None
        self._composite_pass = None
        self._old_composite_shader = None
        self._old_layer_bindings = None

    def beginRendering(self):
        scene = self.getController().getScene()
        renderer = self.getRenderer()

        if not self._xray_shader:
            self._xray_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "xray.shader"))
            self._xray_shader.setUniformValue("u_color", Color(*Application.getInstance().getTheme().getColor("xray").getRgb()))

        for node in BreadthFirstIterator(scene.getRoot()):
            # We do not want to render ConvexHullNode as it conflicts with the bottom of the X-Ray (z-fighting).
            if type(node) is ConvexHullNode:
                continue

            if not node.render(renderer):
                if node.getMeshData() and node.isVisible():
                    renderer.queueNode(node,
                                       shader = self._xray_shader,
                                       type = RenderBatch.RenderType.Solid,
                                       blend_mode = RenderBatch.BlendMode.Additive,
                                       sort = -10,
                                       state_setup_callback = lambda gl: gl.glDepthFunc(gl.GL_ALWAYS),
                                       state_teardown_callback = lambda gl: gl.glDepthFunc(gl.GL_LESS)
                    )

    def endRendering(self):
        pass

    def event(self, event):
        if event.type == Event.ViewActivateEvent:
            # FIX: on Max OS X, somehow QOpenGLContext.currentContext() can become None during View switching.
            # This can happen when you do the following steps:
            #   1. Start Cura
            #   2. Load a model
            #   3. Switch to Custom mode
            #   4. Select the model and click on the per-object tool icon
            #   5. Switch view to Layer view or X-Ray
            #   6. Cura will very likely crash
            # It seems to be a timing issue that the currentContext can somehow be empty, but I have no clue why.
            # This fix tries to reschedule the view changing event call on the Qt thread again if the current OpenGL
            # context is None.
            if Platform.isOSX():
                if QOpenGLContext.currentContext() is None:
                    Logger.log("d", "current context of OpenGL is empty on Mac OS X, will try to create shaders later")
                    CuraApplication.getInstance().callLater(lambda e = event: self.event(e))
                    return

            if not self._xray_pass:
                # Currently the RenderPass constructor requires a size > 0
                # This should be fixed in RenderPass's constructor.
                self._xray_pass = XRayPass.XRayPass(1, 1)

            self.getRenderer().addRenderPass(self._xray_pass)

            if not self._xray_composite_shader:
                self._xray_composite_shader = OpenGL.getInstance().createShaderProgram(os.path.join(PluginRegistry.getInstance().getPluginPath("XRayView"), "xray_composite.shader"))
                theme = Application.getInstance().getTheme()
                self._xray_composite_shader.setUniformValue("u_background_color", Color(*theme.getColor("viewport_background").getRgb()))
                self._xray_composite_shader.setUniformValue("u_error_color", Color(*theme.getColor("xray_error").getRgb()))
                self._xray_composite_shader.setUniformValue("u_outline_color", Color(*theme.getColor("model_selection_outline").getRgb()))

            if not self._composite_pass:
                self._composite_pass = self.getRenderer().getRenderPass("composite")

            self._old_layer_bindings = self._composite_pass.getLayerBindings()
            self._composite_pass.setLayerBindings(["default", "selection", "xray"])
            self._old_composite_shader = self._composite_pass.getCompositeShader()
            self._composite_pass.setCompositeShader(self._xray_composite_shader)

        if event.type == Event.ViewDeactivateEvent:
            self.getRenderer().removeRenderPass(self._xray_pass)
            self._composite_pass.setLayerBindings(self._old_layer_bindings)
            self._composite_pass.setCompositeShader(self._old_composite_shader)
