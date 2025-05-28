# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import numpy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPainter, QColor, QBrush
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
    """Provides the tool to paint meshes.
    """

    def __init__(self) -> None:
        super().__init__()

        self._picking_pass: Optional[PickingPass] = None

        self._shortcut_key: Qt.Key = Qt.Key.Key_P

        self._node_cache: Optional[SceneNode] = None
        self._mesh_transformed_cache = None
        self._cache_dirty: bool = True

        self._color_str_to_rgba: Dict[str, List[int]] = {
            "A": [192, 0, 192, 255],
            "B": [232, 128, 0, 255],
            "C": [0, 255, 0, 255],
            "D": [255, 255, 255, 255],
        }

        self._brush_size: int = 10
        self._brush_color: str = "A"
        self._brush_shape: str = "A"
        self._brush_image = self._createBrushImage()

        self._mouse_held: bool = False
        self._last_text_coords: Optional[Tuple[int, int]] = None

    def _createBrushImage(self) -> QImage:
        brush_image = QImage(self._brush_size, self._brush_size, QImage.Format.Format_RGBA8888)
        brush_image.fill(QColor(255,255,255,0))

        color = self._color_str_to_rgba[self._brush_color]
        qcolor = QColor(color[0], color[1], color[2], color[3])

        painter = QPainter(brush_image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(qcolor))
        match self._brush_shape:
            case "A":  # Square brush
                painter.drawRect(0, 0, self._brush_size, self._brush_size)
            case "B":  # Circle brush
                painter.drawEllipse(0, 0, self._brush_size, self._brush_size)
            case _:
                painter.drawRect(0, 0, self._brush_size, self._brush_size)
        painter.end()

        return brush_image

    def _createStrokeImage(self, x0: float, y0: float, x1: float, y1: float) -> Tuple[QImage, Tuple[int, int]]:
        distance = numpy.hypot(x1 - x0, y1 - y0)
        angle = numpy.arctan2(y1 - y0, x1 - x0)
        stroke_width = self._brush_size
        stroke_height = int(distance) + self._brush_size

        half_brush_size = self._brush_size // 2
        start_x = int(x0 - half_brush_size)
        start_y = int(y0 - half_brush_size)

        stroke_image = QImage(stroke_height, stroke_width, QImage.Format.Format_RGBA8888)
        stroke_image.fill(QColor(255,255,255,0))

        painter = QPainter(stroke_image)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        # rotate the brush-image to follow the stroke-direction
        transform = painter.transform()
        transform.translate(0, stroke_width / 2)  # translate to match the brush-alignment
        transform.rotate(-numpy.degrees(angle))
        painter.setTransform(transform)

        # tile the brush along the stroke-length
        brush_stride = max(1, half_brush_size)
        for i in range(0, int(distance) + brush_stride, brush_stride):
            painter.drawImage(i, -stroke_width, self._brush_image)
        painter.end()

        return stroke_image, (start_x, start_y)

    def setPaintType(self, paint_type: str) -> None:
        Logger.warning(f"TODO: Implement paint-types ({paint_type}).")
        pass  # FIXME: ... and also please call `self._stroke_image = self._createBrushStrokeImage()` (see other funcs).

    def setBrushSize(self, brush_size: float) -> None:
        if brush_size != self._brush_size:
            self._brush_size = int(brush_size)
            self._brush_image = self._createBrushImage()

    def setBrushColor(self, brush_color: str) -> None:
        if brush_color != self._brush_color:
            self._brush_color = brush_color
            self._brush_image = self._createBrushImage()

    def setBrushShape(self, brush_shape: str) -> None:
        if brush_shape != self._brush_shape:
            self._brush_shape = brush_shape
            self._brush_image = self._createBrushImage()

    @staticmethod
    def _get_intersect_ratio_via_pt(a: numpy.ndarray, pt: numpy.ndarray, b: numpy.ndarray, c: numpy.ndarray) -> float:
        # compute the intersection of (param) A - pt with (param) B - (param) C

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

    def _getTexCoordsFromClick(self, node: SceneNode, x: int, y: int) -> Optional[Tuple[float, float]]:
        face_id = self._selection_pass.getFaceIdAtPosition(x, y)
        if face_id < 0:
            return None

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
        return texcoords

    def event(self, event: Event) -> bool:
        """Handle mouse and keyboard events.

        :param event: The event to handle.
        :return: Whether this event has been caught by this tool (True) or should
        be passed on (False).
        """
        super().event(event)

        controller = Application.getInstance().getController()

        # Make sure the displayed values are updated if the bounding box of the selected mesh(es) changes
        if event.type == Event.ToolActivateEvent:
            controller.setActiveStage("PrepareStage")
            controller.setActiveView("PaintTool")  # Because that's the plugin-name, and the view is registered to it.
            return True

        if event.type == Event.ToolDeactivateEvent:
            controller.setActiveStage("PrepareStage")
            controller.setActiveView("SolidView")
            return True

        if event.type == Event.KeyPressEvent and cast(KeyEvent, event).key == KeyEvent.ShiftKey:
            return False

        if event.type == Event.MouseReleaseEvent and self._controller.getToolsEnabled():
            if MouseEvent.LeftButton not in cast(MouseEvent, event).buttons:
                return False
            self._mouse_held = False
            self._last_text_coords = None
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

            node = Selection.getAllSelectedObjects()[0]
            if node is None:
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

            texcoords = self._getTexCoordsFromClick(node, evt.x, evt.y)
            if texcoords is None:
                return False
            if self._last_text_coords is None:
                self._last_text_coords = texcoords

            w, h = paintview.getUvTexDimensions()
            sub_image, (start_x, start_y) = self._createStrokeImage(
                self._last_text_coords[0] * w,
                self._last_text_coords[1] * h,
                texcoords[0] * w,
                texcoords[1] * h
            )
            paintview.addStroke(sub_image, start_x, start_y)

            self._last_text_coords = texcoords
            Application.getInstance().getController().getScene().sceneChanged.emit(node)
            return True

        return False
