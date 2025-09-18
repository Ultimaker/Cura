# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import os

from PyQt6.QtCore import QRect, pyqtSignal
from PyQt6.QtGui import QImage, QUndoStack, QPainter, QColor
from typing import Optional, List, Tuple, Dict

from cura.CuraApplication import CuraApplication
from cura.BuildVolume import BuildVolume
from cura.CuraView import CuraView
from cura.Machines.Models.ExtrudersModel import ExtrudersModel
from UM.PluginRegistry import PluginRegistry
from UM.View.GL.ShaderProgram import ShaderProgram
from UM.View.GL.Texture import Texture
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.Selection import Selection
from UM.View.GL.OpenGL import OpenGL
from UM.i18n import i18nCatalog
from UM.Math.Color import Color

from .PaintUndoCommand import PaintUndoCommand

catalog = i18nCatalog("cura")


class PaintView(CuraView):
    """View for model-painting."""

    class PaintType:
        def __init__(self, display_color: Color, value: int):
            self.display_color: Color = display_color
            self.value: int = value

    def __init__(self) -> None:
        super().__init__(use_empty_menu_placeholder = True)
        self._paint_shader: Optional[ShaderProgram] = None
        self._current_paint_texture: Optional[Texture] = None
        self._previous_paint_texture_stroke: Optional[QRect] = None
        self._cursor_texture: Optional[Texture] = None
        self._current_bits_ranges: tuple[int, int] = (0, 0)
        self._current_paint_type = ""
        self._paint_modes: Dict[str, Dict[str, "PaintView.PaintType"]] = {}

        self._paint_undo_stack: QUndoStack = QUndoStack()
        self._paint_undo_stack.setUndoLimit(32) # Set a quite low amount since every command copies the full texture
        self._paint_undo_stack.canUndoChanged.connect(self.canUndoChanged)
        self._paint_undo_stack.canRedoChanged.connect(self.canRedoChanged)

        application = CuraApplication.getInstance()
        application.engineCreatedSignal.connect(self._makePaintModes)
        self._scene = application.getController().getScene()

        self._extruders_model: Optional[ExtrudersModel] = None

    canUndoChanged = pyqtSignal(bool)
    canRedoChanged = pyqtSignal(bool)

    def canUndo(self):
        return self._paint_undo_stack.canUndo()

    def canRedo(self):
        return self._paint_undo_stack.canRedo()

    def _makePaintModes(self):
        application = CuraApplication.getInstance()

        self._extruders_model = application.getExtrudersModel()
        self._extruders_model.modelChanged.connect(self._onExtrudersChanged)

        theme = application.getTheme()
        usual_types = {"none":      self.PaintType(Color(*theme.getColor("paint_normal_area").getRgb()), 0),
                       "preferred": self.PaintType(Color(*theme.getColor("paint_preferred_area").getRgb()), 1),
                       "avoid":     self.PaintType(Color(*theme.getColor("paint_avoid_area").getRgb()), 2)}
        self._paint_modes = {
            "seam":    usual_types,
            "support": usual_types,
            "extruder": self._makeExtrudersColors(),
        }

        self._current_paint_type = "seam"

    def _makeExtrudersColors(self) -> Dict[str, "PaintView.PaintType"]:
        extruders_colors: Dict[str, "PaintView.PaintType"] = {}

        for extruder_item in self._extruders_model.items:
            if "color" in extruder_item:
                material_color = extruder_item["color"]
            else:
                material_color = self._extruders_model.defaultColors[0]

            index = extruder_item["index"]
            extruders_colors[str(index)] = self.PaintType(Color(*QColor(material_color).getRgb()), index)

        return extruders_colors

    def _onExtrudersChanged(self) -> None:
        if self._paint_modes is None:
            return

        self._paint_modes["extruder"] = self._makeExtrudersColors()

        controller = CuraApplication.getInstance().getController()
        if controller.getActiveView() != self:
            return

        selected_objects = Selection.getAllSelectedObjects()
        if len(selected_objects) != 1:
            return

        controller.getScene().sceneChanged.emit(selected_objects[0])

    def _checkSetup(self):
        if not self._paint_shader:
            shader_filename = os.path.join(PluginRegistry.getInstance().getPluginPath("PaintTool"), "paint.shader")
            self._paint_shader = OpenGL.getInstance().createShaderProgram(shader_filename)

    def setCursorStroke(self, stroke_mask: QImage, start_x: int, start_y: int, brush_color: str):
        if self._cursor_texture is None or self._cursor_texture.getImage() is None:
            return

        self.clearCursorStroke()

        stroke_image = stroke_mask.copy()
        alpha_mask = stroke_image.convertedTo(QImage.Format.Format_Mono)
        stroke_image.setAlphaChannel(alpha_mask)

        painter = QPainter(stroke_image)

        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
        display_color = self._paint_modes[self._current_paint_type][brush_color].display_color
        paint_color = QColor(*[int(color_part * 255) for color_part in [display_color.r, display_color.g, display_color.b]])
        paint_color.setAlpha(255)
        painter.fillRect(0, 0, stroke_mask.width(), stroke_mask.height(), paint_color)

        painter.end()

        self._cursor_texture.setSubImage(stroke_image, start_x, start_y)

        self._previous_paint_texture_stroke = QRect(start_x, start_y, stroke_mask.width(), stroke_mask.height())

    def clearCursorStroke(self) -> bool:
        if (self._previous_paint_texture_stroke is None or
                self._cursor_texture is None or self._cursor_texture.getImage() is None):
            return False

        clear_image = QImage(self._previous_paint_texture_stroke.width(),
                             self._previous_paint_texture_stroke.height(),
                             QImage.Format.Format_ARGB32)
        clear_image.fill(0)
        self._cursor_texture.setSubImage(clear_image,
                                         self._previous_paint_texture_stroke.x(),
                                         self._previous_paint_texture_stroke.y())
        self._previous_paint_texture_stroke = None

        return True

    def addStroke(self, stroke_mask: QImage, start_x: int, start_y: int, brush_color: str, merge_with_previous: bool) -> None:
        if self._current_paint_texture is None or self._current_paint_texture.getImage() is None:
            return

        self._prepareDataMapping()

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

    def getUvTexDimensions(self) -> Tuple[int, int]:
        if self._current_paint_texture is not None:
            return self._current_paint_texture.getWidth(), self._current_paint_texture.getHeight()
        return 0, 0

    def getPaintType(self) -> str:
        return self._current_paint_type

    def setPaintType(self, paint_type: str) -> None:
        self._current_paint_type = paint_type
        self._prepareDataMapping()

    def _prepareDataMapping(self):
        node = Selection.getAllSelectedObjects()[0]
        if node is None:
            return

        paint_data_mapping = node.callDecoration("getTextureDataMapping")

        if self._current_paint_type not in paint_data_mapping:
            new_mapping = self._add_mapping(paint_data_mapping, len(self._paint_modes[self._current_paint_type]))
            paint_data_mapping[self._current_paint_type] = new_mapping
            node.callDecoration("setTextureDataMapping", paint_data_mapping)

        self._current_bits_ranges = paint_data_mapping[self._current_paint_type]

    @staticmethod
    def _add_mapping(actual_mapping: Dict[str, tuple[int, int]], nb_storable_values: int) -> tuple[int, int]:
        start_index = 0
        if actual_mapping:
            start_index = max(end_index for _, end_index in actual_mapping.values()) + 1

        end_index = start_index + int.bit_length(nb_storable_values - 1) - 1

        return start_index, end_index

    def beginRendering(self) -> None:
        if self._current_paint_type not in self._paint_modes:
            return

        self._checkSetup()
        renderer = self.getRenderer()

        for node in DepthFirstIterator(self._scene.getRoot()):
            if isinstance(node, BuildVolume):
                node.render(renderer)

        paint_batch = renderer.createRenderBatch(shader=self._paint_shader)
        renderer.addRenderBatch(paint_batch)

        for node in Selection.getAllSelectedObjects():
            paint_batch.addItem(node.getWorldTransformation(copy=False), node.getMeshData(), normal_transformation=node.getCachedNormalMatrix())
            paint_texture = node.callDecoration("getPaintTexture")
            if paint_texture != self._current_paint_texture:
                self._current_paint_texture = paint_texture
                self._paint_shader.setTexture(0, self._current_paint_texture)

                self._cursor_texture = OpenGL.getInstance().createTexture(paint_texture.getWidth(), paint_texture.getHeight())
                image = QImage(paint_texture.getWidth(), paint_texture.getHeight(), QImage.Format.Format_ARGB32)
                image.fill(0)
                self._cursor_texture.setImage(image)
                self._paint_shader.setTexture(1, self._cursor_texture)
                self._previous_paint_texture_stroke = None

        self._paint_shader.setUniformValue("u_bitsRangesStart", self._current_bits_ranges[0])
        self._paint_shader.setUniformValue("u_bitsRangesEnd", self._current_bits_ranges[1])

        colors = [paint_type_obj.display_color for paint_type_obj in self._paint_modes[self._current_paint_type].values()]
        colors_values = [[int(color_part * 255) for color_part in [color.r, color.g, color.b]] for color in colors]
        self._paint_shader.setUniformValueArray("u_renderColors", colors_values)
