# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from typing import cast, Optional

import numpy
from PyQt6.QtCore import Qt
from typing import Dict, List, Tuple

from UM.Application import Application
from UM.Event import Event, MouseEvent, KeyEvent
from UM.Logger import Logger
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Selection import Selection
from UM.Tool import Tool
from UM.View.View import View
from cura.PickingPass import PickingPass


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

        self._mouse_held: bool = False
        self._mouse_drags: List[Tuple[int, int]] = []

    def setPaintType(self, paint_type: str) -> None:
        Logger.warning(f"TODO: Implement paint-types ({paint_type}).")
        pass

    def setBrushSize(self, brush_size: float) -> None:
        self._brush_size = int(brush_size)
        print(self._brush_size)

    def setBrushColor(self, brush_color: str) -> None:
        self._brush_color = brush_color

    def setBrushShape(self, brush_shape: str) -> None:
        self._brush_shape = brush_shape

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

    def _getBrushPixels(self, mid_x: float, mid_y: float, w: float, h: float) -> List[Tuple[float, float]]:
        res = []
        include = False
        for y in range(-self._brush_size, self._brush_size + 1):
            for x in range(-self._brush_size, self._brush_size + 1):
                match self._brush_shape:
                    case "A":
                        include = True
                    case "B":
                        include = x * x + y * y <= self._brush_size * self._brush_size
                if include:
                    xx = mid_x + (x / w)
                    yy = mid_y + (y / h)
                    if xx < 0 or xx > 1 or yy < 0 or yy > 1:
                        continue
                    res.append((xx, yy))
        return res

    def _handleMouseAction(self, node: SceneNode, paintview: View, x: int, y: int) -> bool:
        face_id = self._selection_pass.getFaceIdAtPosition(x, y)
        if face_id < 0:
            return False

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

        color = self._color_str_to_rgba[self._brush_color]
        w, h = paintview.getUvTexDimensions()
        for (x, y) in self._getBrushPixels(texcoords[0], texcoords[1], float(w), float(h)):
            paintview.setUvPixel(x, y, color)

        return True

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
            drags = self._mouse_drags.copy()
            self._mouse_drags.clear()

            paintview = controller.getActiveView()
            if paintview is None or paintview.getPluginId() != "PaintTool":
                return False

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
            drags.append((evt.x, evt.y))

            if not self._picking_pass:
                self._picking_pass = PickingPass(camera.getViewportWidth(), camera.getViewportHeight())
            self._picking_pass.render()

            self._selection_pass.renderFacesMode()

            res = False
            for (x, y) in drags:
                res |= self._handleMouseAction(node, paintview, x, y)
            return res

        if event.type == Event.MousePressEvent and self._controller.getToolsEnabled():
            if MouseEvent.LeftButton not in cast(MouseEvent, event).buttons:
                return False
            self._mouse_held = True
            return True

        if event.type == Event.MouseMoveEvent:
            if not self._mouse_held:
                return False
            evt = cast(MouseEvent, event)
            self._mouse_drags.append((evt.x, evt.y))
            return True

        return False
