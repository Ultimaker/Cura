# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from enum import IntEnum
import numpy
from PyQt6.QtCore import Qt, QObject, pyqtEnum
from PyQt6.QtGui import QImage, QPainter, QColor, QPen
from PyQt6 import QtWidgets
from typing import cast, Dict, List, Optional, Tuple

from numpy import ndarray

from UM.Application import Application
from UM.Event import Event, MouseEvent, KeyEvent
from UM.Logger import Logger
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Selection import Selection
from UM.Tool import Tool

from cura.PickingPass import PickingPass
from .PaintView import PaintView


class PaintTool(Tool):
    """Provides the tool to paint meshes."""

    class Brush(QObject):
        @pyqtEnum
        class Shape(IntEnum):
            SQUARE = 0
            CIRCLE = 1

    def __init__(self) -> None:
        super().__init__()

        self._picking_pass: Optional[PickingPass] = None

        self._shortcut_key: Qt.Key = Qt.Key.Key_P

        self._node_cache: Optional[SceneNode] = None
        self._mesh_transformed_cache = None
        self._cache_dirty: bool = True

        self._brush_size: int = 10
        self._brush_color: str = ""
        self._brush_shape: PaintTool.Brush.Shape = PaintTool.Brush.Shape.SQUARE
        self._brush_pen: QPen = self._createBrushPen()

        self._mouse_held: bool = False

        self._last_text_coords: Optional[numpy.ndarray] = None
        self._last_mouse_coords: Optional[Tuple[int, int]] = None
        self._last_face_id: Optional[int] = None

    def _createBrushPen(self) -> QPen:
        pen = QPen()
        pen.setWidth(self._brush_size)
        pen.setColor(Qt.GlobalColor.white)

        match self._brush_shape:
            case PaintTool.Brush.Shape.SQUARE:
                pen.setCapStyle(Qt.PenCapStyle.SquareCap)
            case PaintTool.Brush.Shape.CIRCLE:
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        return pen

    def _createStrokeImage(self, x0: float, y0: float, x1: float, y1: float) -> Tuple[QImage, Tuple[int, int]]:
        xdiff = int(x1 - x0)
        ydiff = int(y1 - y0)

        half_brush_size = self._brush_size // 2
        start_x = int(min(x0, x1) - half_brush_size)
        start_y = int(min(y0, y1) - half_brush_size)

        stroke_image = QImage(abs(xdiff) + self._brush_size, abs(ydiff) + self._brush_size, QImage.Format.Format_RGB32)
        stroke_image.fill(0)

        painter = QPainter(stroke_image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setPen(self._brush_pen)
        if xdiff == 0 and ydiff == 0:
            painter.drawPoint(int(x0 - start_x), int(y0 - start_y))
        else:
            painter.drawLine(int(x0 - start_x), int(y0 - start_y), int(x1 - start_x), int(y1 - start_y))
        painter.end()

        return stroke_image, (start_x, start_y)

    def setPaintType(self, paint_type: str) -> None:
        paint_view = self._get_paint_view()
        if paint_view is None:
            return

        paint_view.setPaintType(paint_type)

        self._brush_pen = self._createBrushPen()
        self._updateScene()

    def setBrushSize(self, brush_size: float) -> None:
        if brush_size != self._brush_size:
            self._brush_size = int(brush_size)
            self._brush_pen = self._createBrushPen()

    def setBrushColor(self, brush_color: str) -> None:
        self._brush_color = brush_color

    def setBrushShape(self, brush_shape: int) -> None:
        if brush_shape != self._brush_shape:
            self._brush_shape = brush_shape
            self._brush_pen = self._createBrushPen()

    def undoStackAction(self, redo_instead: bool) -> bool:
        paint_view = self._get_paint_view()
        if paint_view is None:
            return False

        if redo_instead:
            paint_view.redoStroke()
        else:
            paint_view.undoStroke()

        self._updateScene()
        return True

    def clear(self) -> None:
        paintview = self._get_paint_view()
        if paintview is None:
            return

        width, height = paintview.getUvTexDimensions()
        clear_image = QImage(width, height, QImage.Format.Format_RGB32)
        clear_image.fill(Qt.GlobalColor.white)
        paintview.addStroke(clear_image, 0, 0, "none")

        self._updateScene()

    @staticmethod
    def _get_paint_view() -> Optional[PaintView]:
        paint_view = Application.getInstance().getController().getActiveView()
        if paint_view is None or paint_view.getPluginId() != "PaintTool":
            return None
        return cast(PaintView, paint_view)

    @staticmethod
    def _get_intersect_ratio_via_pt(a: numpy.ndarray, pt: numpy.ndarray, b: numpy.ndarray, c: numpy.ndarray) -> float:
        # compute the intersection of (param) A - pt with (param) B - (param) C
        if all(a == pt) or all(b == c) or all(a == c) or all(a == b):
            return 1.0

        # compute unit vectors of directions of lines A and B
        udir_a = a - pt
        udir_a /= numpy.linalg.norm(udir_a)
        udir_b = b - c
        udir_b /= numpy.linalg.norm(udir_b)

        # find unit direction vector for line C, which is perpendicular to lines A and B
        udir_res = numpy.cross(udir_b, udir_a)
        udir_res_len = numpy.linalg.norm(udir_res)
        if udir_res_len == 0:
            return 1.0
        udir_res /= udir_res_len

        # solve system of equations
        rhs = b - a
        lhs = numpy.array([udir_a, -udir_b, udir_res]).T
        try:
            solved = numpy.linalg.solve(lhs, rhs)
        except numpy.linalg.LinAlgError:
            return 1.0

        # get the ratio
        intersect = ((a + solved[0] * udir_a) + (b + solved[1] * udir_b)) * 0.5
        a_intersect_dist = numpy.linalg.norm(a - intersect)
        if a_intersect_dist == 0:
            return 1.0
        return numpy.linalg.norm(pt - intersect) / a_intersect_dist

    def _nodeTransformChanged(self, *args) -> None:
        self._cache_dirty = True

    def _getTexCoordsFromClick(self, node: SceneNode, x: float, y: float) -> Tuple[int, Optional[numpy.ndarray]]:
        face_id = self._selection_pass.getFaceIdAtPosition(x, y)
        if face_id < 0 or face_id >= node.getMeshData().getFaceCount():
            return face_id, None

        pt = self._picking_pass.getPickedPosition(x, y).getData()

        va, vb, vc = self._mesh_transformed_cache.getFaceNodes(face_id)

        face_uv_coordinates = node.getMeshData().getFaceUvCoords(face_id)
        if face_uv_coordinates is None:
            return face_id, None
        ta, tb, tc = face_uv_coordinates

        # 'Weight' of each vertex that would produce point pt, so we can generate the texture coordinates from the uv ones of the vertices.
        # See (also) https://mathworld.wolfram.com/BarycentricCoordinates.html
        wa = PaintTool._get_intersect_ratio_via_pt(va, pt, vb, vc)
        wb = PaintTool._get_intersect_ratio_via_pt(vb, pt, vc, va)
        wc = PaintTool._get_intersect_ratio_via_pt(vc, pt, va, vb)
        wt = wa + wb + wc
        if wt == 0:
            return face_id, None
        wa /= wt
        wb /= wt
        wc /= wt
        texcoords = wa * ta + wb * tb + wc * tc
        return face_id, texcoords

    def _iteratateSplitSubstroke(self, node, substrokes,
                                 info_a: Tuple[Tuple[float, float], Tuple[int, Optional[numpy.ndarray]]],
                                 info_b: Tuple[Tuple[float, float], Tuple[int, Optional[numpy.ndarray]]]) -> None:
        click_a, (face_a, texcoords_a) = info_a
        click_b, (face_b, texcoords_b) = info_b

        if (abs(click_a[0] - click_b[0]) < 0.0001 and abs(click_a[1] - click_b[1]) < 0.0001) or (face_a < 0 and face_b < 0):
            return
        if face_b < 0 or face_a == face_b:
            substrokes.append((self._last_text_coords, texcoords_a))
            return
        if face_a < 0:
            substrokes.append((self._last_text_coords, texcoords_b))
            return

        mouse_mid = (click_a[0] + click_b[0]) / 2.0, (click_a[1] + click_b[1]) / 2.0
        face_mid, texcoords_mid = self._getTexCoordsFromClick(node, mouse_mid[0], mouse_mid[1])
        mid_struct = (mouse_mid, (face_mid, texcoords_mid))
        if face_mid == face_a:
            substrokes.append((texcoords_a, texcoords_mid))
            self._iteratateSplitSubstroke(node, substrokes, mid_struct, info_b)
        elif face_mid == face_b:
            substrokes.append((texcoords_mid, texcoords_b))
            self._iteratateSplitSubstroke(node, substrokes, info_a, mid_struct)
        else:
            self._iteratateSplitSubstroke(node, substrokes, mid_struct, info_b)
            self._iteratateSplitSubstroke(node, substrokes, info_a, mid_struct)

    def event(self, event: Event) -> bool:
        """Handle mouse and keyboard events.

        :param event: The event to handle.
        :return: Whether this event has been caught by this tool (True) or should
        be passed on (False).
        """
        super().event(event)

        controller = Application.getInstance().getController()
        node = Selection.getSelectedObject(0)
        if node is None:
            return False

        # Make sure the displayed values are updated if the bounding box of the selected mesh(es) changes
        if event.type == Event.ToolActivateEvent:
            controller.setActiveStage("PrepareStage")
            controller.setActiveView("PaintTool")  # Because that's the plugin-name, and the view is registered to it.
            return True

        if event.type == Event.ToolDeactivateEvent:
            controller.setActiveStage("PrepareStage")
            controller.setActiveView("SolidView")
            return True

        if event.type == Event.MouseReleaseEvent and self._controller.getToolsEnabled():
            if MouseEvent.LeftButton not in cast(MouseEvent, event).buttons:
                return False
            self._mouse_held = False
            self._last_text_coords = None
            self._last_mouse_coords = None
            self._last_face_id = None
            return True

        is_moved = event.type == Event.MouseMoveEvent
        is_pressed = event.type == Event.MousePressEvent
        if (is_moved or is_pressed) and self._controller.getToolsEnabled():
            if is_moved and not self._mouse_held:
                return False

            mouse_evt = cast(MouseEvent, event)
            if is_pressed:
                if MouseEvent.LeftButton not in mouse_evt.buttons:
                    return False
                else:
                    self._mouse_held = True

            paintview = self._get_paint_view()
            if paintview is None:
                return False

            if not self._selection_pass:
                return False

            camera = self._controller.getScene().getActiveCamera()
            if not camera:
                return False

            if node != self._node_cache:
                if self._node_cache is not None:
                    self._node_cache.transformationChanged.disconnect(self._nodeTransformChanged)
                self._node_cache = node
                self._node_cache.transformationChanged.connect(self._nodeTransformChanged)
            if self._cache_dirty:
                self._cache_dirty = False
                self._mesh_transformed_cache = self._node_cache.getMeshDataTransformed()
            if not self._mesh_transformed_cache:
                return False

            if not self._picking_pass:
                self._picking_pass = PickingPass(camera.getViewportWidth(), camera.getViewportHeight())
            self._picking_pass.render()

            self._selection_pass.renderFacesMode()

            face_id, texcoords = self._getTexCoordsFromClick(node, mouse_evt.x, mouse_evt.y)
            if texcoords is None:
                return False
            if self._last_text_coords is None:
                self._last_text_coords = texcoords
                self._last_mouse_coords = (mouse_evt.x, mouse_evt.y)
                self._last_face_id = face_id

            substrokes = []
            if face_id == self._last_face_id:
                substrokes.append((self._last_text_coords, texcoords))
            else:
                self._iteratateSplitSubstroke(node, substrokes,
                                              (self._last_mouse_coords, (self._last_face_id, self._last_text_coords)),
                                              ((mouse_evt.x, mouse_evt.y), (face_id, texcoords)))

            w, h = paintview.getUvTexDimensions()
            for start_coords, end_coords in substrokes:
                sub_image, (start_x, start_y) = self._createStrokeImage(
                    start_coords[0] * w,
                    start_coords[1] * h,
                    end_coords[0] * w,
                    end_coords[1] * h
                )
                paintview.addStroke(sub_image, start_x, start_y, self._brush_color)

            self._last_text_coords = texcoords
            self._last_mouse_coords = (mouse_evt.x, mouse_evt.y)
            self._last_face_id = face_id
            self._updateScene(node)
            return True

        return False

    @staticmethod
    def _updateScene(node: SceneNode = None):
        if node is None:
            node = Selection.getSelectedObject(0)
        if node is not None:
            Application.getInstance().getController().getScene().sceneChanged.emit(node)