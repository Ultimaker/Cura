# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import os
from typing import Optional, List, Tuple

from PyQt6.QtGui import QImage, QColor, QPainter

from UM.PluginRegistry import PluginRegistry
from UM.View.GL.ShaderProgram import ShaderProgram
from UM.View.GL.Texture import Texture
from UM.View.View import View
from UM.Scene.Selection import Selection
from UM.View.GL.OpenGL import OpenGL
from UM.i18n import i18nCatalog

catalog = i18nCatalog("cura")


class PaintView(View):
    """View for model-painting."""

    UNDO_STACK_SIZE = 1024

    def __init__(self) -> None:
        super().__init__()
        self._paint_shader: Optional[ShaderProgram] = None
        self._paint_texture: Optional[Texture] = None

        # FIXME: When the texture UV-unwrapping is done, these two values will need to be set to a proper value (suggest 4096 for both).
        self._tex_width = 512
        self._tex_height = 512

        self._stroke_undo_stack: List[Tuple[QImage, int, int]] = []
        self._stroke_redo_stack: List[Tuple[QImage, int, int]] = []

        self._force_opaque_mask = QImage(2, 2, QImage.Format.Format_Mono)
        self._force_opaque_mask.fill(1)

    def _checkSetup(self):
        if not self._paint_shader:
            shader_filename = os.path.join(PluginRegistry.getInstance().getPluginPath("PaintTool"), "paint.shader")
            self._paint_shader = OpenGL.getInstance().createShaderProgram(shader_filename)
        if not self._paint_texture:
            self._paint_texture = OpenGL.getInstance().createTexture(self._tex_width, self._tex_height)
            self._paint_shader.setTexture(0, self._paint_texture)

    def _forceOpaqueDeepCopy(self, image: QImage):
        res = QImage(image.width(), image.height(), QImage.Format.Format_RGBA8888)
        res.fill(QColor(255, 255, 255, 255))
        painter = QPainter(res)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.drawImage(0, 0, image)
        painter.end()
        res.setAlphaChannel(self._force_opaque_mask.scaled(image.width(), image.height()))
        return res

    def addStroke(self, stroke_image: QImage, start_x: int, start_y: int) -> None:
        self._stroke_redo_stack.clear()
        if len(self._stroke_undo_stack) >= PaintView.UNDO_STACK_SIZE:
            self._stroke_undo_stack.pop(0)
        undo_image = self._forceOpaqueDeepCopy(self._paint_texture.setSubImage(stroke_image, start_x, start_y))
        if undo_image is not None:
            self._stroke_undo_stack.append((undo_image, start_x, start_y))

    def _applyUndoStacksAction(self, from_stack: List[Tuple[QImage, int, int]], to_stack: List[Tuple[QImage, int, int]]) -> bool:
        if len(from_stack) <= 0:
            return False
        from_image, x, y = from_stack.pop()
        to_image = self._forceOpaqueDeepCopy(self._paint_texture.setSubImage(from_image, x, y))
        if to_image is None:
            return False
        if len(to_stack) >= PaintView.UNDO_STACK_SIZE:
            to_stack.pop(0)
        to_stack.append((to_image, x, y))
        return True

    def undoStroke(self) -> bool:
        return self._applyUndoStacksAction(self._stroke_undo_stack, self._stroke_redo_stack)

    def redoStroke(self) -> bool:
        return self._applyUndoStacksAction(self._stroke_redo_stack, self._stroke_undo_stack)

    def getUvTexDimensions(self):
        return self._tex_width, self._tex_height

    def beginRendering(self) -> None:
        renderer = self.getRenderer()
        self._checkSetup()
        paint_batch = renderer.createRenderBatch(shader=self._paint_shader)
        renderer.addRenderBatch(paint_batch)

        node = Selection.getSelectedObject(0)
        if node is None:
            return
        paint_batch.addItem(node.getWorldTransformation(copy=False), node.getMeshData(), normal_transformation=node.getCachedNormalMatrix())
