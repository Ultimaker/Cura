# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import os
import math

from PyQt6.QtCore import QRect, pyqtSignal, Qt, QPoint
from PyQt6.QtGui import QImage, QUndoStack, QPainter, QColor, QPainterPath, QBrush, QPen
from typing import Optional, List, Tuple, Dict

from UM.Scene.SceneNode import SceneNode
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

from .PaintStrokeCommand import PaintStrokeCommand
from .PaintClearCommand import PaintClearCommand

catalog = i18nCatalog("cura")


class PaintView(CuraView):
    """View for model-painting."""

    MAX_EXTRUDER_COUNT = 16

    class PaintType:
        def __init__(self, display_color: Color, value: int):
            self.display_color: Color = display_color
            self.value: int = value

    def __init__(self) -> None:
        super().__init__(use_empty_menu_placeholder = True)
        self._paint_shader: Optional[ShaderProgram] = None
        self._current_paint_texture: Optional[Texture] = None
        self._current_painted_object: Optional[SceneNode] = None
        self._previous_paint_texture_rect: Optional[QRect] = None
        self._cursor_texture: Optional[Texture] = None
        self._current_bits_ranges: tuple[int, int] = (0, 0)
        self._current_paint_type = ""
        self._paint_modes: Dict[str, Dict[str, "PaintView.PaintType"]] = {}
        self._paint_undo_stacks: Dict[Tuple[SceneNode, str], QUndoStack] = {}

        application = CuraApplication.getInstance()
        application.engineCreatedSignal.connect(self._makePaintModes)
        self._scene = application.getController().getScene()
        self._scene.getRoot().childrenChanged.connect(self._onChildrenChanged)

        self._extruders_model: Optional[ExtrudersModel] = None

    canUndoChanged = pyqtSignal(bool)
    canRedoChanged = pyqtSignal(bool)

    def setCurrentPaintedObject(self, current_painted_object: Optional[SceneNode]):
        self._current_painted_object = current_painted_object

    def canUndo(self):
        stack = self._getUndoStack()
        return stack.canUndo() if stack is not None else False

    def canRedo(self):
        stack = self._getUndoStack()
        return stack.canRedo() if stack is not None else False

    def _getUndoStack(self):
        if self._current_painted_object is None or self._current_paint_type == "":
            return None

        try:
            return self._paint_undo_stacks[(self._current_painted_object, self._current_paint_type)]
        except KeyError:
            return None

    def _onChildrenChanged(self, root_node: SceneNode):
        # Gather all the actual nodes that have one or more undo stacks
        stacks_keys = {}
        for painted_object, paint_mode in self._paint_undo_stacks:
            if painted_object in stacks_keys:
                stacks_keys[painted_object].append(paint_mode)
            else:
                stacks_keys[painted_object] = [paint_mode]

        # Now see if any of the nodes have been deleted, i.e. they are no more linked to the root
        for painted_object, paint_modes in stacks_keys.items():
            if painted_object.getDepth() == 0:
                for paint_mode in paint_modes:
                    del self._paint_undo_stacks[(painted_object, paint_mode)]

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

        for extruder_index in range(PaintView.MAX_EXTRUDER_COUNT):
            extruder_item = self._extruders_model.getExtruderItem(extruder_index)
            if extruder_item is None:
                extruder_item = self._extruders_model.getExtruderItem(0)

            if extruder_item is not None and "color" in extruder_item:
                material_color = extruder_item["color"]
            else:
                material_color = self._extruders_model.defaultColors[0]

            extruders_colors[str(extruder_index)] = self.PaintType(Color(*QColor(material_color).getRgb()), extruder_index)

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

    def setCursorStroke(self, cursor_path: QPainterPath, brush_color: str):
        if self._cursor_texture is None or self._cursor_texture.getImage() is None:
            return

        self.clearCursorStroke()

        bounding_rect = cursor_path.boundingRect()
        bounding_rect_rounded = QRect(
            QPoint(math.floor(bounding_rect.left()), math.floor(bounding_rect.top())),
            QPoint(math.ceil(bounding_rect.right()), math.ceil(bounding_rect.bottom())))

        cursor_image = QImage(bounding_rect_rounded.width(), bounding_rect_rounded.height(), QImage.Format.Format_ARGB32)
        cursor_image.fill(0)

        painter = QPainter(cursor_image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.translate(-bounding_rect.left(), -bounding_rect.top())
        display_color = self._paint_modes[self._current_paint_type][brush_color].display_color
        paint_color = QColor(*[int(color_part * 255) for color_part in [display_color.r, display_color.g, display_color.b]])
        paint_color.setAlpha(255)
        painter.setBrush(QBrush(paint_color))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawPath(cursor_path)

        painter.end()

        self._cursor_texture.setSubImage(cursor_image, bounding_rect_rounded.left(), bounding_rect_rounded.top())

        self._previous_paint_texture_rect = bounding_rect_rounded

    def clearCursorStroke(self) -> bool:
        if (self._previous_paint_texture_rect is None or
                self._cursor_texture is None or self._cursor_texture.getImage() is None):
            return False

        clear_image = QImage(self._previous_paint_texture_rect.width(),
                             self._previous_paint_texture_rect.height(),
                             QImage.Format.Format_ARGB32)
        clear_image.fill(0)
        self._cursor_texture.setSubImage(clear_image,
                                         self._previous_paint_texture_rect.left(),
                                         self._previous_paint_texture_rect.top())
        self._previous_paint_texture_rect = None

        return True

    def addStroke(self, stroke_path: QPainterPath, brush_color: str, merge_with_previous: bool) -> None:
        if self._current_paint_texture is None or self._current_paint_texture.getImage() is None:
            return

        self._prepareDataMapping()
        stack = self._prepareUndoRedoStack()

        bit_range_start, bit_range_end = self._current_bits_ranges
        set_value = self._paint_modes[self._current_paint_type][brush_color].value << bit_range_start

        stack.push(PaintStrokeCommand(self._current_paint_texture,
                                      stroke_path,
                                      set_value,
                                      (bit_range_start, bit_range_end),
                                      merge_with_previous))

    def clearPaint(self):
        if self._current_paint_texture is None or self._current_paint_texture.getImage() is None:
            return

        self._prepareDataMapping()
        stack = self._prepareUndoRedoStack()
        stack.push(PaintClearCommand(self._current_paint_texture, self._current_bits_ranges))

    def undoStroke(self) -> None:
        stack = self._getUndoStack()
        if stack is not None:
            stack.undo()

    def redoStroke(self) -> None:
        stack = self._getUndoStack()
        if stack is not None:
            stack.redo()

    def getUvTexDimensions(self) -> Tuple[int, int]:
        if self._current_paint_texture is not None:
            return self._current_paint_texture.getWidth(), self._current_paint_texture.getHeight()
        return 0, 0

    def getPaintType(self) -> str:
        return self._current_paint_type

    def setPaintType(self, paint_type: str) -> None:
        self._current_paint_type = paint_type
        self._prepareDataMapping()

    def _prepareUndoRedoStack(self) -> QUndoStack:
        stack_key = (self._current_painted_object, self._current_paint_type)

        if stack_key not in self._paint_undo_stacks:
            stack: QUndoStack = QUndoStack()
            stack.setUndoLimit(32)  # Set a quite low amount since some commands copy the full texture
            stack.canUndoChanged.connect(self.canUndoChanged)
            stack.canRedoChanged.connect(self.canRedoChanged)
            self._paint_undo_stacks[stack_key] = stack

        return self._paint_undo_stacks[stack_key]

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
            if paint_texture != self._current_paint_texture and paint_texture is not None:
                self._current_paint_texture = paint_texture

                self._cursor_texture = OpenGL.getInstance().createTexture(paint_texture.getWidth(), paint_texture.getHeight())
                self._paint_shader.setTexture(0, self._current_paint_texture)
                image = QImage(paint_texture.getWidth(), paint_texture.getHeight(), QImage.Format.Format_ARGB32)
                image.fill(0)
                self._cursor_texture.setImage(image)
                self._paint_shader.setTexture(1, self._cursor_texture)

        self._paint_shader.setUniformValue("u_bitsRangesStart", self._current_bits_ranges[0])
        self._paint_shader.setUniformValue("u_bitsRangesEnd", self._current_bits_ranges[1])

        colors = [paint_type_obj.display_color for paint_type_obj in self._paint_modes[self._current_paint_type].values()]
        colors_values = [[int(color_part * 255) for color_part in [color.r, color.g, color.b]] for color in colors]
        self._paint_shader.setUniformValueArray("u_renderColors", colors_values)
