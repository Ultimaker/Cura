# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import os
from PyQt6.QtGui import QImage

from UM.PluginRegistry import PluginRegistry
from UM.View.View import View
from UM.Scene.Selection import Selection
from UM.View.GL.OpenGL import OpenGL
from UM.i18n import i18nCatalog

catalog = i18nCatalog("cura")


class PaintView(View):
    """View for model-painting."""

    def __init__(self) -> None:
        super().__init__()
        self._paint_shader = None
        self._paint_texture = None

        # FIXME: When the texture UV-unwrapping is done, these two values will need to be set to a proper value (suggest 4096 for both).
        self._tex_width = 512
        self._tex_height = 512

    def _checkSetup(self):
        if not self._paint_shader:
            shader_filename = os.path.join(PluginRegistry.getInstance().getPluginPath("PaintTool"), "paint.shader")
            self._paint_shader = OpenGL.getInstance().createShaderProgram(shader_filename)
        if not self._paint_texture:
            self._paint_texture = OpenGL.getInstance().createTexture(self._tex_width, self._tex_height)
            self._paint_shader.setTexture(0, self._paint_texture)

    def addStroke(self, stroke_image: QImage, start_x: int, start_y: int) -> None:
        self._paint_texture.setSubImage(stroke_image, start_x, start_y)

    def getUvTexDimensions(self):
        return self._tex_width, self._tex_height

    def beginRendering(self) -> None:
        renderer = self.getRenderer()
        self._checkSetup()
        paint_batch = renderer.createRenderBatch(shader=self._paint_shader)
        renderer.addRenderBatch(paint_batch)

        node = Selection.getAllSelectedObjects()[0]
        if node is None:
            return
        paint_batch.addItem(node.getWorldTransformation(copy=False), node.getMeshData(), normal_transformation=node.getCachedNormalMatrix())
