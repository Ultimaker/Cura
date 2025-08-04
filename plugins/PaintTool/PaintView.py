# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import os
from PyQt6.QtCore import QRect
from typing import Optional, List, Tuple, Dict

from PyQt6.QtGui import QImage, QColor, QPainter, QUndoStack

from cura.CuraApplication import CuraApplication
from UM.PluginRegistry import PluginRegistry
from UM.View.GL.ShaderProgram import ShaderProgram
from UM.View.GL.Texture import Texture
from UM.View.View import View
from UM.Scene.Selection import Selection
from UM.View.GL.OpenGL import OpenGL
from UM.i18n import i18nCatalog
from UM.Math.Color import Color

from .PaintUndoCommand import PaintUndoCommand

catalog = i18nCatalog("cura")


class PaintView(View):
    """View for model-painting."""

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

        self._paint_undo_stack: QUndoStack = QUndoStack()
        self._paint_undo_stack.setUndoLimit(32) # Set a quite low amount since every command copies the full texture

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

    def addStroke(self, stroke_mask: QImage, start_x: int, start_y: int, brush_color: str, merge_with_previous: bool) -> None:
        if self._current_paint_texture is None or self._current_paint_texture.getImage() is None:
            return

        current_image = self._current_paint_texture.getImage()
        texture_rect = QRect(0, 0, current_image.width(), current_image.height())
        stroke_rect = QRect(start_x, start_y, stroke_mask.width(), stroke_mask.height())
        intersect_rect = texture_rect.intersected(stroke_rect)
        if intersect_rect != stroke_rect:
            # Stroke doesn't fully fit into the image, we have to crop it
            stroke_mask = stroke_mask.copy(intersect_rect.x() - start_x,
                                           intersect_rect.y() - start_y,
                                           intersect_rect.width(),
                                           intersect_rect.height())
            start_x = intersect_rect.x()
            start_y = intersect_rect.y()

        bit_range_start, bit_range_end = self._current_bits_ranges
        set_value = self._paint_modes[self._current_paint_type][brush_color].value << bit_range_start

        self._paint_undo_stack.push(PaintUndoCommand(self._current_paint_texture,
                                                     stroke_mask,
                                                     start_x,
                                                     start_y,
                                                     set_value,
                                                     (bit_range_start, bit_range_end),
                                                     merge_with_previous))

    def undoStroke(self) -> None:
        self._paint_undo_stack.undo()

    def redoStroke(self) -> None:
        self._paint_undo_stack.redo()

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
