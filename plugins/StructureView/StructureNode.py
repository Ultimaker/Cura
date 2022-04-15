# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Resources import Resources
from UM.View.GL.OpenGL import OpenGL
from UM.Scene.SceneNode import SceneNode

class StructureNode(SceneNode):
    def __init__(self, parent):
        super().__init__(parent)
        self._shader = None

    def render(self, renderer):
        if not self.isVisible():
            return True
        if not self._shader:
            self._shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "default.shader"))

        if self.getMeshData():
            renderer.queueNode(self, shader = self._shader, transparent = False, backface_cull = False)
            return True
        return False