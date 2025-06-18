# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from enum import IntEnum
import numpy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPainter, QColor, QBrush, QPen
from typing import cast, Dict, List, Optional, Tuple

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

    class BrushShape(IntEnum):
        SQUARE = 0
        CIRCLE = 1

    def __init__(self) -> None:
        super().__init__()

        self._picking_pass: Optional[PickingPass] = None

        self._shortcut_key: Qt.Key = Qt.Key.Key_P

        self._node_cache: Optional[SceneNode] = None
        self._mesh_transformed_cache = None
        self._cache_dirty: bool = True

        # TODO: Colors will need to be replaced on a 'per type of painting' basis.
        self._color_str_to_rgba: Dict[str, List[int]] = {
            "A": [192, 0, 192, 255],
            "B": [232, 128, 0, 255],
            "C": [0, 255, 0, 255],
            "D": [255, 255, 255, 255],
        }

        self._brush_size: int = 10
        self._brush_color: str = "A"
        self._brush_shape: PaintTool.BrushShape = PaintTool.BrushShape.SQUARE
        self._brush_pen: QPen = self._createBrushPen()

        self._mouse_held: bool = False
        self._ctrl_held: bool = False
        self._shift_held: bool = False

        self._last_text_coords: Optional[numpy.ndarray] = None
        self._last_face_id: Optional[int] = None

    def _createBrushPen(self) -> QPen:
        pen = QPen()
        pen.setWidth(self._brush_size)
        color = self._color_str_to_rgba[self._brush_color]
        pen.setColor(QColor(color[0], color[1], color[2], color[3]))
        match self._brush_shape:
            case PaintTool.BrushShape.SQUARE:
                pen.setCapStyle(Qt.PenCapStyle.SquareCap)
            case PaintTool.BrushShape.CIRCLE:
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        return pen

    def _createStrokeImage(self, x0: float, y0: float, x1: float, y1: float) -> Tuple[QImage, Tuple[int, int]]:
        xdiff = int(x1 - x0)
        ydiff = int(y1 - y0)

        half_brush_size = self._brush_size // 2
        start_x = int(min(x0, x1) - half_brush_size)
        start_y = int(min(y0, y1) - half_brush_size)

        stroke_image = QImage(abs(xdiff) + self._brush_size, abs(ydiff) + self._brush_size, QImage.Format.Format_RGBA8888)
        stroke_image.fill(QColor(0,0,0,0))

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
        Logger.warning(f"TODO: Implement paint-types ({paint_type}).")
        pass  # FIXME: ... and also please call `self._brush_pen = self._createBrushPen()` (see other funcs).

    def setBrushSize(self, brush_size: float) -> None:
        if brush_size != self._brush_size:
            self._brush_size = int(brush_size)
            self._brush_pen = self._createBrushPen()

    def setBrushColor(self, brush_color: str) -> None:
        if brush_color != self._brush_color:
            self._brush_color = brush_color
            self._brush_pen = self._createBrushPen()

    def setBrushShape(self, brush_shape: int) -> None:
        if brush_shape != self._brush_shape:
            self._brush_shape = brush_shape
            self._brush_pen = self._createBrushPen()

    def undoStackAction(self, redo_instead: bool) -> bool:
        paintview = Application.getInstance().getController().getActiveView()
        if paintview is None or paintview.getPluginId() != "PaintTool":
            return False
        paintview = cast(PaintView, paintview)
        if redo_instead:
            paintview.redoStroke()
        else:
            paintview.undoStroke()
        node = Selection.getSelectedObject(0)
        if node is not None:
            Application.getInstance().getController().getScene().sceneChanged.emit(node)
        return True

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
        udir_res /= numpy.linalg.norm(udir_res)

        # solve system of equations
        rhs = b - a
        lhs = numpy.array([udir_a, -udir_b, udir_res]).T
        solved = numpy.linalg.solve(lhs, rhs)

        # get the ratio
        intersect = ((a + solved[0] * udir_a) + (b + solved[1] * udir_b)) * 0.5
        return numpy.linalg.norm(pt - intersect) / numpy.linalg.norm(a - intersect)

    def _nodeTransformChanged(self, *args) -> None:
        self._cache_dirty = True

    def _getTexCoordsFromClick(self, node: SceneNode, x: int, y: int) -> Tuple[int, Optional[numpy.ndarray]]:
        face_id = self._selection_pass.getFaceIdAtPosition(x, y)
        if face_id < 0 or face_id >= node.getMeshData().getFaceCount():
            return face_id, None

        pt = self._picking_pass.getPickedPosition(x, y).getData()

        va, vb, vc = self._mesh_transformed_cache.getFaceNodes(face_id)
        ta, tb, tc = node.getMeshData().getFaceUvCoords(face_id)

        # 'Weight' of each vertex that would produce point pt, so we can generate the texture coordinates from the uv ones of the vertices.
        # See (also) https://mathworld.wolfram.com/BarycentricCoordinates.html
        wa = PaintTool._get_intersect_ratio_via_pt(va, pt, vb, vc)
        wb = PaintTool._get_intersect_ratio_via_pt(vb, pt, vc, va)
        wc = PaintTool._get_intersect_ratio_via_pt(vc, pt, va, vb)
        wt = wa + wb + wc
        wa /= wt
        wb /= wt
        wc /= wt
        texcoords = wa * ta + wb * tb + wc * tc
        return face_id, texcoords

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

        if event.type == Event.KeyPressEvent:
            evt = cast(KeyEvent, event)
            if evt.key == KeyEvent.ControlKey:
                self._ctrl_held = True
                return True
            if evt.key == KeyEvent.ShiftKey:
                self._shift_held = True
                return True
            return False

        if event.type == Event.KeyReleaseEvent:
            evt = cast(KeyEvent, event)
            if evt.key == KeyEvent.ControlKey:
                self._ctrl_held = False
                return True
            if evt.key == KeyEvent.ShiftKey:
                self._shift_held = False
                return True
            if evt.key == Qt.Key.Key_L and self._ctrl_held:
                # NOTE: Ctrl-L is used here instead of Ctrl-Z, as the latter is the application-wide one that takes precedence.
                return self.undoStackAction(self._shift_held)
            return False

        if event.type == Event.MouseReleaseEvent and self._controller.getToolsEnabled():
            if MouseEvent.LeftButton not in cast(MouseEvent, event).buttons:
                return False
            self._mouse_held = False
            self._last_text_coords = None
            self._last_face_id = None
            return True

        is_moved = event.type == Event.MouseMoveEvent
        is_pressed = event.type == Event.MousePressEvent
        if (is_moved or is_pressed) and self._controller.getToolsEnabled():
            if is_moved and not self._mouse_held:
                return False

            evt = cast(MouseEvent, event)
            if is_pressed:
                if MouseEvent.LeftButton not in evt.buttons:
                    return False
                else:
                    self._mouse_held = True

            paintview = controller.getActiveView()
            if paintview is None or paintview.getPluginId() != "PaintTool":
                return False
            paintview = cast(PaintView, paintview)

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

            evt = cast(MouseEvent, event)

            if not self._picking_pass:
                self._picking_pass = PickingPass(camera.getViewportWidth(), camera.getViewportHeight())
            self._picking_pass.render()

            self._selection_pass.renderFacesMode()

            face_id, texcoords = self._getTexCoordsFromClick(node, evt.x, evt.y)
            if texcoords is None:
                return False
            if self._last_text_coords is None:
                self._last_text_coords = texcoords
                self._last_face_id = face_id

            if face_id != self._last_face_id:
                # TODO: draw two strokes in this case, for the two faces involved
                #       ... it's worse, for smaller faces we may genuinely require the patch -- and it may even go over _multiple_ patches if the user paints fast enough
                #       -> for now; make a lookup table for which faces are connected to which, don't split if they are connected, and solve the connection issue(s) later
                self._last_text_coords = texcoords
                self._last_face_id = face_id
                return True

            w, h = paintview.getUvTexDimensions()
            sub_image, (start_x, start_y) = self._createStrokeImage(
                self._last_text_coords[0] * w,
                self._last_text_coords[1] * h,
                texcoords[0] * w,
                texcoords[1] * h
            )
            paintview.addStroke(sub_image, start_x, start_y)

            self._last_text_coords = texcoords
            self._last_face_id = face_id
            Application.getInstance().getController().getScene().sceneChanged.emit(node)
            return True

        return False
