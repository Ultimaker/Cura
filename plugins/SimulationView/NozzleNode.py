# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Application import Application
from UM.Math.Color import Color
from UM.PluginRegistry import PluginRegistry
from UM.Scene.SceneNode import SceneNode
from UM.View.GL.OpenGL import OpenGL
from UM.Resources import Resources

import os

class NozzleNode(SceneNode):
    def __init__(self, parent = None):
        super().__init__(parent)

        self._shader = None
        self.setCalculateBoundingBox(False)
        self._createNozzleMesh()

    def _createNozzleMesh(self):
        mesh_file = "resources/nozzle.stl"
        try:
            path = os.path.join(PluginRegistry.getInstance().getPluginPath("SimulationView"), mesh_file)
        except FileNotFoundError:
            path = ""

        reader = Application.getInstance().getMeshFileHandler().getReaderForFile(path)
        node = reader.read(path)

        if node.getMeshData():
            self.setMeshData(node.getMeshData())

    def render(self, renderer):
        # Avoid to render if it is not visible
        if not self.isVisible():
            return False

        if not self._shader:
            # We now misuse the platform shader, as it actually supports textures
            self._shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "color.shader"))
            self._shader.setUniformValue("u_color", Color(*Application.getInstance().getTheme().getColor("layerview_nozzle").getRgb()))
            # Set the opacity to 0, so that the template is in full control.
            self._shader.setUniformValue("u_opacity", 0)

        if self.getMeshData():
            renderer.queueNode(self, shader = self._shader, transparent = True)
            return True
