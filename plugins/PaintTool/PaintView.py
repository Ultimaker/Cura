# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import os
import math
from weakref import WeakKeyDictionary

from PyQt6.QtCore import QRect, pyqtSignal, Qt, QPoint
from PyQt6.QtGui import QImage, QUndoStack, QPainter, QColor, QPainterPath, QBrush, QPen
from typing import Optional, Tuple, Dict, List

from UM.Logger import Logger
from UM.Scene.SceneNode import SceneNode
from cura.CuraApplication import CuraApplication
from cura.BuildVolume import BuildVolume
from cura.CuraView import CuraView
from cura.Machines.Models.ExtrudersModel import ExtrudersModel
from UM.PluginRegistry import PluginRegistry
from UM.View.GL.ShaderProgram import ShaderProgram
from UM.View.GL.Texture import Texture
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.View.GL.OpenGL import OpenGL
from UM.i18n import i18nCatalog
from UM.Math.Color import Color
from UM.Math.Polygon import Polygon
from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator

from .PaintStrokeCommand import PaintStrokeCommand
from .PaintClearCommand import PaintClearCommand
from .MultiMaterialExtruderConverter import MultiMaterialExtruderConverter

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
        self._paint_texture: Optional[Texture] = None
        self._painted_object: Optional[SceneNode] = None
        self._previous_paint_texture_rect: Optional[QRect] = None
        self._cursor_texture: Optional[Texture] = None
        self._current_bits_ranges: tuple[int, int] = (0, 0)
        self._current_paint_type = ""
        self._paint_modes: Dict[str, Dict[str, "PaintView.PaintType"]] = {}
        self._paint_undo_stacks: WeakKeyDictionary[SceneNode, Dict[str, QUndoStack]] = WeakKeyDictionary()

        application = CuraApplication.getInstance()
        application.engineCreatedSignal.connect(self._makePaintModes)
        self._scene = application.getController().getScene()

        self._extruders_model: Optional[ExtrudersModel] = None
        self._extruders_converter: Optional[MultiMaterialExtruderConverter] = None

    canUndoChanged = pyqtSignal(bool)
    canRedoChanged = pyqtSignal(bool)

    def setPaintedObject(self, painted_object: Optional[SceneNode]):
        if self._painted_object is not None:
            texture_changed_signal = self._painted_object.callDecoration("getPaintTextureChangedSignal")
            texture_changed_signal.disconnect(self._onCurrentPaintedObjectTextureChanged)

        self._paint_texture = None
        self._cursor_texture = None

        self._painted_object = None

        if painted_object is not None and painted_object.callDecoration("isSliceable"):
            self._painted_object = painted_object
            texture_changed_signal = self._painted_object.callDecoration("getPaintTextureChangedSignal")
            if texture_changed_signal is not None:
                texture_changed_signal.connect(self._onCurrentPaintedObjectTextureChanged)
            self._onCurrentPaintedObjectTextureChanged()

        self._updateCurrentBitsRanges()

    def getPaintedObject(self) -> Optional[SceneNode]:
        return self._painted_object

    def hasPaintedObject(self) -> bool:
        return self._painted_object is not None

    def _onCurrentPaintedObjectTextureChanged(self) -> None:
        paint_texture = self._painted_object.callDecoration("getPaintTexture")
        self._paint_texture = paint_texture
        if paint_texture is not None:
            self._cursor_texture = OpenGL.getInstance().createTexture(paint_texture.getWidth(),
                                                                      paint_texture.getHeight())
            image = QImage(paint_texture.getWidth(), paint_texture.getHeight(), QImage.Format.Format_ARGB32)
            image.fill(0)
            self._cursor_texture.setImage(image)
        else:
            self._cursor_texture = None

    def canUndo(self):
        stack = self._getUndoStack()
        return stack.canUndo() if stack is not None else False

    def canRedo(self):
        stack = self._getUndoStack()
        return stack.canRedo() if stack is not None else False

    def _getUndoStack(self):
        if self._painted_object is None:
            return None

        try:
            return self._paint_undo_stacks[self._painted_object][self._current_paint_type]
        except KeyError:
            return None

    def _makePaintModes(self):
        application = CuraApplication.getInstance()

        self._extruders_model = application.getExtrudersModel()
        self._extruders_model.modelChanged.connect(self._onExtrudersChanged)

        self._extruders_converter = MultiMaterialExtruderConverter(self._extruders_model)
        self._extruders_converter.mainExtruderChanged.connect(self._onMainExtruderChanged)

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

    def _onMainExtruderChanged(self, node: SceneNode):
        # Since the affected extruder has changed, the previous material painting commands become irrelevant,
        # so clear the undo stack of the object, if any
        try:
            self._paint_undo_stacks[node]["extruder"].clear()
        except KeyError:
            pass

    def _makeExtrudersColors(self) -> Dict[str, "PaintView.PaintType"]:
        extruders_colors: Dict[str, "PaintView.PaintType"] = {}

        for extruder_index in range(MultiMaterialExtruderConverter.MAX_EXTRUDER_COUNT):
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

        if self._painted_object is None:
            return

        controller.getScene().sceneChanged.emit(self._painted_object)

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

        painter = QPainter(self._cursor_texture.getImage())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        display_color = self._paint_modes[self._current_paint_type][brush_color].display_color
        paint_color = QColor(*[int(color_part * 255) for color_part in [display_color.r, display_color.g, display_color.b]])
        paint_color.setAlpha(255)
        painter.setBrush(QBrush(paint_color))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawPath(cursor_path)
        painter.end()

        self._cursor_texture.updateImagePart(bounding_rect_rounded)
        self._previous_paint_texture_rect = bounding_rect_rounded

    def clearCursorStroke(self) -> bool:
        if (self._previous_paint_texture_rect is None or
                self._cursor_texture is None or self._cursor_texture.getImage() is None):
            return False

        painter = QPainter(self._cursor_texture.getImage())
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self._previous_paint_texture_rect, QBrush(QColor(0, 0, 0, 0)))
        painter.end()

        self._cursor_texture.updateImagePart(self._previous_paint_texture_rect)
        self._previous_paint_texture_rect = None

        return True

    def _shiftTextureValue(self, value: int) -> int:
        if self._current_bits_ranges is None:
            return 0

        bit_range_start, _ = self._current_bits_ranges
        return value << bit_range_start

    def addStroke(self, stroke_path: List[Polygon], brush_color: str, merge_with_previous: bool) -> None:
        if self._paint_texture is None or self._paint_texture.getImage() is None:
            return

        self._prepareDataMapping()
        stack = self._prepareUndoRedoStack()

        if stack is None:
            return

        set_value = self._shiftTextureValue(self._paint_modes[self._current_paint_type][brush_color].value)
        stack.push(PaintStrokeCommand(self._paint_texture,
                                      stroke_path,
                                      set_value,
                                      self._current_bits_ranges,
                                      merge_with_previous,
                                      self._getSliceableObjectDecorator()))

    def _getSliceableObjectDecorator(self) -> Optional[SliceableObjectDecorator]:
        if self._painted_object is None or self._current_paint_type != "extruder":
            return None

        return self._painted_object.getDecorator(SliceableObjectDecorator)

    def _makeClearCommand(self) -> Optional[PaintClearCommand]:
        if self._painted_object is None or self._paint_texture is None or self._current_bits_ranges is None:
            return None

        set_value = 0
        if self._current_paint_type == "extruder":
            extruder_stack = self._painted_object.getPrintingExtruder()
            if extruder_stack is not None:
                set_value = extruder_stack.getValue("extruder_nr")

        return PaintClearCommand(self._paint_texture,
                                 self._current_bits_ranges,
                                 self._shiftTextureValue(set_value),
                                 self._getSliceableObjectDecorator())

    def clearPaint(self):
        self._prepareDataMapping()
        stack = self._prepareUndoRedoStack()

        if stack is None:
            return

        clear_command = self._makeClearCommand()
        if clear_command is not None:
            stack.push(clear_command)

    def undoStroke(self) -> None:
        stack = self._getUndoStack()
        if stack is not None:
            stack.undo()

    def redoStroke(self) -> None:
        stack = self._getUndoStack()
        if stack is not None:
            stack.redo()

    def getUvTexDimensions(self) -> Tuple[int, int]:
        if self._paint_texture is not None:
            return self._paint_texture.getWidth(), self._paint_texture.getHeight()
        return 0, 0

    def getPaintType(self) -> str:
        return self._current_paint_type

    def setPaintType(self, paint_type: str) -> None:
        self._current_paint_type = paint_type
        self._prepareDataMapping()

    def _prepareUndoRedoStack(self) -> Optional[QUndoStack]:
        if self._painted_object is None:
            return None

        try:
            return self._paint_undo_stacks[self._painted_object][self._current_paint_type]
        except KeyError:
            stack: QUndoStack = QUndoStack()
            stack.setUndoLimit(16)  # Set a quite low amount since some commands copy the full texture
            stack.canUndoChanged.connect(self.canUndoChanged)
            stack.canRedoChanged.connect(self.canRedoChanged)

            if self._painted_object not in self._paint_undo_stacks:
                self._paint_undo_stacks[self._painted_object] = {}

            self._paint_undo_stacks[self._painted_object][self._current_paint_type] = stack
            return stack

    def _updateCurrentBitsRanges(self):
        self._current_bits_ranges = (0, 0)

        if self._painted_object is None:
            return

        paint_data_mapping = self._painted_object.callDecoration("getTextureDataMapping")
        if paint_data_mapping is None or self._current_paint_type not in paint_data_mapping:
            return

        self._current_bits_ranges = paint_data_mapping[self._current_paint_type]

    def _prepareDataMapping(self):
        if self._painted_object is None:
            return

        paint_data_mapping = self._painted_object.callDecoration("getTextureDataMapping")

        feature_created = False
        if self._current_paint_type not in paint_data_mapping:
            new_mapping = self._add_mapping(paint_data_mapping, len(self._paint_modes[self._current_paint_type]))
            paint_data_mapping[self._current_paint_type] = new_mapping
            self._painted_object.callDecoration("setTextureDataMapping", paint_data_mapping)
            feature_created = True

        self._updateCurrentBitsRanges()

        if feature_created and self._current_paint_type == "extruder":
            # Fill texture extruder with actual mesh extruder
            clear_command = self._makeClearCommand()
            if clear_command is not None:
                clear_command.redo()

    @staticmethod
    def _add_mapping(actual_mapping: Dict[str, tuple[int, int]], nb_storable_values: int) -> tuple[int, int]:
        start_index = 0
        if actual_mapping:
            start_index = max(end_index for _, end_index in actual_mapping.values()) + 1

        end_index = start_index + int.bit_length(nb_storable_values - 1) - 1

        return start_index, end_index

    def beginRendering(self) -> None:
        if self._painted_object is None or self._current_paint_type not in self._paint_modes:
            return

        self._checkSetup()
        renderer = self.getRenderer()

        for node in DepthFirstIterator(self._scene.getRoot()):
            if isinstance(node, BuildVolume):
                node.render(renderer)

        paint_batch = renderer.createRenderBatch(shader=self._paint_shader)
        renderer.addRenderBatch(paint_batch)

        paint_batch.addItem(self._painted_object.getWorldTransformation(copy=False),
                            self._painted_object.getMeshData(),
                            normal_transformation=self._painted_object.getCachedNormalMatrix())

        if self._paint_texture is not None:
            self._paint_shader.setTexture(0, self._paint_texture)
        if self._cursor_texture is not None:
            self._paint_shader.setTexture(1, self._cursor_texture)

        self._paint_shader.setUniformValue("u_bitsRangesStart", self._current_bits_ranges[0])
        self._paint_shader.setUniformValue("u_bitsRangesEnd", self._current_bits_ranges[1])

        if self._current_bits_ranges[0] != self._current_bits_ranges[1]:
            colors = [paint_type_obj.display_color for paint_type_obj in self._paint_modes[self._current_paint_type].values()]
        elif self._current_paint_type == "extruder":
            object_extruder = MultiMaterialExtruderConverter.getPaintedObjectExtruderNr(self._painted_object)
            colors = [self._paint_modes[self._current_paint_type][str(object_extruder)].display_color]
        else:
            colors = [self._paint_modes[self._current_paint_type]["none"].display_color]

        colors_values = [[int(color_part * 255) for color_part in [color.r, color.g, color.b]] for color in colors]
        self._paint_shader.setUniformValueArray("u_renderColors", colors_values)
