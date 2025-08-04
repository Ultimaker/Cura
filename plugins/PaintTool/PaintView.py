# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import os
from PyQt6.QtCore import QRect
from typing import Optional, List, Tuple, Dict

from PyQt6.QtGui import QImage, QColor, QPainter

from cura.CuraApplication import CuraApplication
from UM.PluginRegistry import PluginRegistry
from UM.View.GL.ShaderProgram import ShaderProgram
from UM.View.GL.Texture import Texture
from UM.View.View import View
from UM.Scene.Selection import Selection
from UM.View.GL.OpenGL import OpenGL
from UM.i18n import i18nCatalog
from UM.Math.Color import Color

catalog = i18nCatalog("cura")


class PaintView(View):
    """View for model-painting."""

    UNDO_STACK_SIZE = 1024

    class PaintType:
        def __init__(self, display_color: Color, value: int):
            self.display_color: Color = display_color
            self.value: int = value

    def __init__(self) -> None:
        super().__init__()
        self._paint_shader: Optional[ShaderProgram] = None
        self._current_paint_texture: Optional[Texture] = None
        self._current_bits_ranges: tuple[int, int] = (0, 0)
        self._current_paint_type = ""
        self._paint_modes: Dict[str, Dict[str, "PaintView.PaintType"]] = {}

        self._stroke_undo_stack: List[Tuple[QImage, int, int]] = []
        self._stroke_redo_stack: List[Tuple[QImage, int, int]] = []

        self._force_opaque_mask = QImage(2, 2, QImage.Format.Format_Mono)
        self._force_opaque_mask.fill(1)

        CuraApplication.getInstance().engineCreatedSignal.connect(self._makePaintModes)

    def _makePaintModes(self):
        theme = CuraApplication.getInstance().getTheme()
        usual_types = {"none":      self.PaintType(Color(*theme.getColor("paint_normal_area").getRgb()), 0),
                       "preferred": self.PaintType(Color(*theme.getColor("paint_preferred_area").getRgb()), 1),
                       "avoid":     self.PaintType(Color(*theme.getColor("paint_avoid_area").getRgb()), 2)}
        self._paint_modes = {
            "seam":    usual_types,
            "support": usual_types,
        }

    def _checkSetup(self):
        if not self._paint_shader:
            shader_filename = os.path.join(PluginRegistry.getInstance().getPluginPath("PaintTool"), "paint.shader")
            self._paint_shader = OpenGL.getInstance().createShaderProgram(shader_filename)

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

    def addStroke(self, stroke_mask: QImage, start_x: int, start_y: int, brush_color: str) -> None:
        if self._current_paint_texture is None or self._current_paint_texture.getImage() is None:
            return

        actual_image = self._current_paint_texture.getImage()

        bit_range_start, bit_range_end = self._current_bits_ranges
        set_value = self._paint_modes[self._current_paint_type][brush_color].value << self._current_bits_ranges[0]
        full_int32 = 0xffffffff
        clear_mask = full_int32 ^ (((full_int32 << (32 - 1 - (bit_range_end - bit_range_start))) & full_int32) >> (32 - 1 - bit_range_end))
        image_rect = QRect(0, 0, stroke_mask.width(), stroke_mask.height())

        clear_bits_image = stroke_mask.copy()
        clear_bits_image.invertPixels()
        painter = QPainter(clear_bits_image)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Lighten)
        painter.fillRect(image_rect, clear_mask)
        painter.end()

        set_value_image = stroke_mask.copy()
        painter = QPainter(set_value_image)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)
        painter.fillRect(image_rect, set_value)
        painter.end()

        stroked_image = actual_image.copy(start_x, start_y, stroke_mask.width(), stroke_mask.height())
        painter = QPainter(stroked_image)
        painter.setCompositionMode(QPainter.CompositionMode.RasterOp_SourceAndDestination)
        painter.drawImage(0, 0, clear_bits_image)
        painter.setCompositionMode(QPainter.CompositionMode.RasterOp_SourceOrDestination)
        painter.drawImage(0, 0, set_value_image)
        painter.end()

        self._stroke_redo_stack.clear()
        if len(self._stroke_undo_stack) >= PaintView.UNDO_STACK_SIZE:
            self._stroke_undo_stack.pop(0)
        undo_image = self._forceOpaqueDeepCopy(self._current_paint_texture.setSubImage(stroked_image, start_x, start_y))
        if undo_image is not None:
            self._stroke_undo_stack.append((undo_image, start_x, start_y))

    def _applyUndoStacksAction(self, from_stack: List[Tuple[QImage, int, int]], to_stack: List[Tuple[QImage, int, int]]) -> bool:
        if len(from_stack) <= 0 or self._current_paint_texture is None:
            return False
        from_image, x, y = from_stack.pop()
        to_image = self._forceOpaqueDeepCopy(self._current_paint_texture.setSubImage(from_image, x, y))
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
        if self._current_paint_texture is not None:
            return self._current_paint_texture.getWidth(), self._current_paint_texture.getHeight()
        return 0, 0

    def setPaintType(self, paint_type: str) -> None:
        node = Selection.getAllSelectedObjects()[0]
        if node is None:
            return

        paint_data_mapping = node.callDecoration("getTextureDataMapping")

        if paint_type not in paint_data_mapping:
            new_mapping = self._add_mapping(paint_data_mapping, len(self._paint_modes[paint_type]))
            paint_data_mapping[paint_type] = new_mapping
            node.callDecoration("setTextureDataMapping", paint_data_mapping)

        mesh = node.getMeshData()
        if not mesh.hasUVCoordinates():
            texture_width, texture_height = mesh.calculateUnwrappedUVCoordinates()
            if texture_width > 0 and texture_height > 0:
                node.callDecoration("prepareTexture", texture_width, texture_height)

            if hasattr(mesh, OpenGL.VertexBufferProperty):
                # Force clear OpenGL buffer so that new UV coordinates will be sent
                delattr(mesh, OpenGL.VertexBufferProperty)

        self._current_paint_type = paint_type
        self._current_bits_ranges = paint_data_mapping[paint_type]

    @staticmethod
    def _add_mapping(actual_mapping: Dict[str, tuple[int, int]], nb_storable_values: int) -> tuple[int, int]:
        start_index = 0
        if actual_mapping:
            start_index = max(end_index for _, end_index in actual_mapping.values()) + 1

        end_index = start_index + int.bit_length(nb_storable_values - 1) - 1

        return start_index, end_index

    def beginRendering(self) -> None:
        renderer = self.getRenderer()
        self._checkSetup()
        paint_batch = renderer.createRenderBatch(shader=self._paint_shader)
        renderer.addRenderBatch(paint_batch)

        node = Selection.getSelectedObject(0)
        if node is None:
            return

        if self._current_paint_type == "":
            return

        self._paint_shader.setUniformValue("u_bitsRangesStart", self._current_bits_ranges[0])
        self._paint_shader.setUniformValue("u_bitsRangesEnd", self._current_bits_ranges[1])

        colors = [paint_type_obj.display_color for paint_type_obj in self._paint_modes[self._current_paint_type].values()]
        colors_values = [[int(color_part * 255) for color_part in [color.r, color.g, color.b]] for color in colors]
        self._paint_shader.setUniformValueArray("u_renderColors", colors_values)

        self._current_paint_texture = node.callDecoration("getPaintTexture")
        self._paint_shader.setTexture(0, self._current_paint_texture)

        paint_batch.addItem(node.getWorldTransformation(copy=False), node.getMeshData(), normal_transformation=node.getCachedNormalMatrix())
