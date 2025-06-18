# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import os
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
        def __init__(self, icon: str, display_color: Color, value: int):
            self.icon: str = icon
            self.display_color: Color = display_color
            self.value: int = value

    class PaintMode:
        def __init__(self, icon: str, types: Dict[str, "PaintView.PaintType"]):
            self.icon: str = icon
            self.types = types

    def __init__(self) -> None:
        super().__init__()
        self._paint_shader: Optional[ShaderProgram] = None
        self._current_paint_texture: Optional[Texture] = None
        self._current_bits_ranges: tuple[int, int] = (0, 0)
        self._current_paint_type = ""
        self._paint_modes: Dict[str, PaintView.PaintMode] = {}

        self._stroke_undo_stack: List[Tuple[QImage, int, int]] = []
        self._stroke_redo_stack: List[Tuple[QImage, int, int]] = []

        self._force_opaque_mask = QImage(2, 2, QImage.Format.Format_Mono)
        self._force_opaque_mask.fill(1)

        CuraApplication.getInstance().engineCreatedSignal.connect(self._makePaintModes)

    def _makePaintModes(self):
        theme = CuraApplication.getInstance().getTheme()
        usual_types = {"A": self.PaintType("Buildplate", Color(*theme.getColor("paint_normal_area").getRgb()), 0),
                       "B": self.PaintType("BlackMagic", Color(*theme.getColor("paint_preferred_area").getRgb()), 1),
                       "C": self.PaintType("Eye", Color(*theme.getColor("paint_avoid_area").getRgb()), 2)}
        self._paint_modes = {
            "A": self.PaintMode("MeshTypeNormal", usual_types),
            "B": self.PaintMode("CircleOutline", usual_types),
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

    def addStroke(self, stroke_image: QImage, start_x: int, start_y: int, brush_color: str) -> None:
        if self._current_paint_texture is None or self._current_paint_texture.getImage() is None:
            return

        actual_image = self._current_paint_texture.getImage()

        bit_range_start, bit_range_end = self._current_bits_ranges
        set_value = self._paint_modes[self._current_paint_type].types[brush_color].value << self._current_bits_ranges[0]
        clear_mask = 0xffffffff ^ (((0xffffffff << (32 - 1 - (bit_range_end - bit_range_start))) & 0xffffffff) >> (32 - 1 - bit_range_end))

        for x in range(stroke_image.width()):
            for y in range(stroke_image.height()):
                stroke_pixel = stroke_image.pixel(x, y)
                actual_pixel = actual_image.pixel(start_x + x, start_y + y)
                if stroke_pixel != 0:
                    new_pixel = (actual_pixel & clear_mask) | set_value
                else:
                    new_pixel = actual_pixel
                stroke_image.setPixel(x, y, new_pixel)

        self._stroke_redo_stack.clear()
        if len(self._stroke_undo_stack) >= PaintView.UNDO_STACK_SIZE:
            self._stroke_undo_stack.pop(0)
        undo_image = self._forceOpaqueDeepCopy(self._current_paint_texture.setSubImage(stroke_image, start_x, start_y))
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
            new_mapping = self._add_mapping(paint_data_mapping, len(self._paint_modes[paint_type].types))
            paint_data_mapping[paint_type] = new_mapping
            node.callDecoration("setTextureDataMapping", paint_data_mapping)

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
            self.setPaintType("A")

        self._paint_shader.setUniformValue("u_bitsRangesStart", self._current_bits_ranges[0])
        self._paint_shader.setUniformValue("u_bitsRangesEnd", self._current_bits_ranges[1])

        colors = [paint_type_obj.display_color for paint_type_obj in self._paint_modes[self._current_paint_type].types.values()]
        colors_values = [[int(color_part * 255) for color_part in [color.r, color.g, color.b]] for color in colors]
        self._paint_shader.setUniformValueArray("u_renderColors", colors_values)

        self._current_paint_texture = node.callDecoration("getPaintTexture")
        self._paint_shader.setTexture(0, self._current_paint_texture)

        paint_batch.addItem(node.getWorldTransformation(copy=False), node.getMeshData(), normal_transformation=node.getCachedNormalMatrix())
