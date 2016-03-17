# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.View.View import View
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Resources import Resources
from UM.Application import Application
from UM.Preferences import Preferences
from UM.View.Renderer import Renderer

from UM.View.GL.OpenGL import OpenGL

import math

## Standard view for mesh models. 
class SolidView(View):
    def __init__(self):
        super().__init__()

        Preferences.getInstance().addPreference("view/show_overhang", True)

        self._enabled_shader = None
        self._disabled_shader = None

    def beginRendering(self):
        scene = self.getController().getScene()
        renderer = self.getRenderer()

        if not self._enabled_shader:
            self._enabled_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "overhang.shader"))

        if not self._disabled_shader:
            self._disabled_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "overhang.shader"))
            self._disabled_shader.setUniformValue("u_diffuseColor", [0.68, 0.68, 0.68, 1.0])
            self._disabled_shader.setUniformValue("u_overhangAngle", math.cos(math.radians(0)))

        if Application.getInstance().getMachineManager().getWorkingProfile():
            profile = Application.getInstance().getMachineManager().getWorkingProfile()

            if Preferences.getInstance().getValue("view/show_overhang"):
                angle = profile.getSettingValue("support_angle")
                if angle != None:
                    self._enabled_shader.setUniformValue("u_overhangAngle", math.cos(math.radians(90 - angle)))
                else:
                    self._enabled_shader.setUniformValue("u_overhangAngle", math.cos(math.radians(0))) #Overhang angle of 0 causes no area at all to be marked as overhang.
            else:
                self._enabled_shader.setUniformValue("u_overhangAngle", math.cos(math.radians(0)))

        for node in DepthFirstIterator(scene.getRoot()):
            if not node.render(renderer):
                if node.getMeshData() and node.isVisible():
                    # TODO: Find a better way to handle this
                    #if node.getBoundingBoxMesh():
                    #    renderer.queueNode(scene.getRoot(), mesh = node.getBoundingBoxMesh(),mode = Renderer.RenderLines)
                    if hasattr(node, "_outside_buildarea"):
                        if node._outside_buildarea:
                            renderer.queueNode(node, shader = self._disabled_shader)
                        else:
                            renderer.queueNode(node, shader = self._enabled_shader)
                    else:
                        renderer.queueNode(node, material = self._enabled_shader)
                if node.callDecoration("isGroup"):
                    renderer.queueNode(scene.getRoot(), mesh = node.getBoundingBoxMesh(),mode = Renderer.RenderLines)

    def endRendering(self):
        pass

    #def _onPreferenceChanged(self, preference):
        #if preference == "view/show_overhang": ## Todo: This a printer only setting. Should be removed from Uranium.
            #self._enabled_material = None
