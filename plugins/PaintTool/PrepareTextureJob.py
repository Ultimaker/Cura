# Copyright (c) 2025 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Job import Job
from UM.Scene.SceneNode import SceneNode
from UM.View.GL.OpenGL import OpenGL


class PrepareTextureJob(Job):
    """
    Background job to prepare a model for painting, i.e. do the UV-unwrapping and create the appropriate texture image,
    which can last a few seconds
    """

    def __init__(self, node: SceneNode):
        super().__init__()
        self._node: SceneNode = node

    def run(self) -> None:
        # If the model has already-provided UV coordinates, we can only assume that the associated texture
        # should be a square
        texture_width = texture_height = 4096

        mesh = self._node.getMeshData()
        if not mesh.hasUVCoordinates():
            texture_width, texture_height = mesh.calculateUnwrappedUVCoordinates()

        self._node.callDecoration("prepareTexture", texture_width, texture_height)

        if hasattr(mesh, OpenGL.VertexBufferProperty):
            # Force clear OpenGL buffer so that new UV coordinates will be sent
            delattr(mesh, OpenGL.VertexBufferProperty)

