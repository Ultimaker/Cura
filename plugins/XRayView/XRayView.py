# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import os.path

from UM.PluginRegistry import PluginRegistry
from UM.Event import Event
from UM.View.View import View
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator

from UM.View.GL.OpenGL import OpenGL

from . import XRayPass

## View used to display g-code paths.
class XRayView(View):
    def __init__(self):
        super().__init__()
        self._shader = None

        self._xray_pass = None
        self._xray_composite_shader = None
        self._composite_pass = None
        self._old_composite_shader = None
        self._old_layer_bindings = None

    def beginRendering(self):
        scene = self.getController().getScene()
        renderer = self.getRenderer()

        for node in DepthFirstIterator(scene.getRoot()):
            node.render(renderer)

    def endRendering(self):
        pass

    def event(self, event):
        renderer = self.getRenderer()
        if event.type == Event.ViewActivateEvent:
            if not self._xray_pass:
                self._xray_pass = XRayPass.XRayPass(1280, 720)
                renderer.addRenderPass(self._xray_pass)

            if not self._xray_composite_shader:
                self._xray_composite_shader = OpenGL.getInstance().createShaderProgram(os.path.join(PluginRegistry.getInstance().getPluginPath("XRayView"), "xray_composite.shader"))

            if not self._composite_pass:
                self._composite_pass = renderer.getRenderPass("composite")

            self._old_layer_bindings = self._composite_pass.getLayerBindings()
            self._composite_pass.setLayerBindings(["default", "selection", "xray"])
            self._old_composite_shader = self._composite_pass.getCompositeShader()
            self._composite_pass.setCompositeShader(self._xray_composite_shader)

        if event.type == Event.ViewDeactivateEvent:
            self._composite_pass.setLayerBindings(self._old_layer_bindings)
            self._composite_pass.setCompositeShader(self._old_composite_shader)
