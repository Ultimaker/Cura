# Copyright (c) 2025 3Dconnexion, UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Scene.SceneNode import SceneNode
from UM.View.GL.OpenGL import OpenGL
from UM.Mesh.MeshBuilder import MeshBuilder  # To create the overlay quad
from UM.Resources import Resources  # To find shader locations
from UM.Math.Matrix import Matrix
from UM.Application import Application

try:
    from PyQt6.QtGui import QImage
except:
    from PyQt5.QtGui import QImage

class OverlayNode(SceneNode):
    def __init__(self, node, image_path, size, parent=None):
        super().__init__(parent)
        self._target_node = node
        self.setCalculateBoundingBox(False)

        self._overlay_mesh = self._createOverlayQuad(size)
        self._drawed_mesh = self._overlay_mesh
        self._shader = None
        self._scene = Application.getInstance().getController().getScene()
        self._scale = 1.
        self._image_path = image_path

    def scale(self, factor):
        scale_matrix = Matrix()
        scale_matrix.setByScaleFactor(factor)
        self._drawed_mesh = self._overlay_mesh.getTransformed(scale_matrix)

    def _createOverlayQuad(self, size):
        mb = MeshBuilder()
        mb.addFaceByPoints(-size / 2, -size / 2, 0, -size / 2, size / 2, 0, size / 2, -size / 2, 0)
        mb.addFaceByPoints(size / 2, size / 2, 0, -size / 2, size / 2, 0, size / 2, -size / 2, 0)

        # Set UV coordinates so a texture can be created
        mb.setVertexUVCoordinates(0, 0, 1)
        mb.setVertexUVCoordinates(1, 0, 0)
        mb.setVertexUVCoordinates(4, 0, 0)
        mb.setVertexUVCoordinates(2, 1, 1)
        mb.setVertexUVCoordinates(5, 1, 1)
        mb.setVertexUVCoordinates(3, 1, 0)

        return mb.build()

    def render(self, renderer):

        if not self._shader:
            # We now misuse the platform shader, as it actually supports textures
            self._shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "platform.shader"))
            # Set the opacity to 0, so that the template is in full control.
            self._shader.setUniformValue("u_opacity", 0)
            self._texture = OpenGL.getInstance().createTexture()
            texture_image = QImage(self._image_path)
            self._texture.setImage(texture_image)
            self._shader.setTexture(0, self._texture)

        node_position = self._target_node.getWorldPosition()
        position_matrix = Matrix()
        position_matrix.setByTranslation(node_position)
        camera_orientation = self._scene.getActiveCamera().getOrientation().toMatrix()

        renderer.queueNode(self._scene.getRoot(), shader=self._shader, mesh=self._drawed_mesh.getTransformed(position_matrix.multiply(camera_orientation)), overlay=True)

        return True  # This node does it's own rendering.
