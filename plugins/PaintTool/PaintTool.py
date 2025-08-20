# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from enum import IntEnum
import numpy
from PyQt6.QtCore import Qt, QObject, pyqtEnum
from PyQt6.QtGui import QImage, QPainter, QPen, QPainterPath
from typing import cast, Optional, Tuple, List

from UM.Application import Application
from UM.Event import Event, MouseEvent
from UM.Job import Job
from UM.Logger import Logger
from UM.Math.Polygon import Polygon
from UM.Mesh.MeshData import MeshData
from UM.Scene.Camera import Camera
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Selection import Selection
from UM.Tool import Tool

from cura.CuraApplication import CuraApplication
from cura.PickingPass import PickingPass
from UM.View.SelectionPass import SelectionPass
from .PaintView import PaintView
from .PrepareTextureJob import PrepareTextureJob


class PaintTool(Tool):
    """Provides the tool to paint meshes."""

    class Brush(QObject):
        @pyqtEnum
        class Shape(IntEnum):
            SQUARE = 0
            CIRCLE = 1

    class Paint(QObject):
        @pyqtEnum
        class State(IntEnum):
            MULTIPLE_SELECTION = 0 # Multiple objects are selected, wait until there is only one
            PREPARING_MODEL = 1    # Model is being prepared (UV-unwrapping, texture generation)
            READY = 2              # Ready to paint !

    def __init__(self) -> None:
        super().__init__()

        self._picking_pass: Optional[PickingPass] = None
        self._faces_selection_pass: Optional[SelectionPass] = None

        self._shortcut_key: Qt.Key = Qt.Key.Key_P

        self._node_cache: Optional[SceneNode] = None
        self._mesh_transformed_cache = None
        self._cache_dirty: bool = True

        self._brush_size: int = 200
        self._brush_color: str = "preferred"
        self._brush_shape: PaintTool.Brush.Shape = PaintTool.Brush.Shape.CIRCLE
        self._brush_pen: QPen = self._createBrushPen()

        self._mouse_held: bool = False

        self._last_world_coords: Optional[numpy.ndarray] = None
        self._last_face_id: Optional[int] = None

        self._state: PaintTool.Paint.State = PaintTool.Paint.State.MULTIPLE_SELECTION
        self._prepare_texture_job: Optional[PrepareTextureJob] = None

        self.setExposedProperties("PaintType", "BrushSize", "BrushColor", "BrushShape", "State")

        self._controller.activeViewChanged.connect(self._updateIgnoreUnselectedObjects)
        self._controller.activeToolChanged.connect(self._updateState)

        self._camera: Optional[Camera] = None
        self._cam_pos: numpy.ndarray = numpy.array([0.0, 0.0, 0.0])
        self._cam_norm: numpy.ndarray = numpy.array([0.0, 0.0, 1.0])
        self._cam_axis_q: numpy.ndarray = numpy.array([1.0, 0.0, 0.0])
        self._cam_axis_r: numpy.ndarray = numpy.array([0.0, -1.0, 0.0])

    def _updateCamera(self, *args) -> None:
        if self._camera is None:
            self._camera = Application.getInstance().getController().getScene().getActiveCamera()
            self._camera.transformationChanged.connect(self._updateCamera)
        self._cam_pos = self._camera.getPosition().getData()
        cam_ray = self._camera.getRay(0, 0)
        self._cam_norm = cam_ray.direction.getData()
        self._cam_norm /= -numpy.linalg.norm(self._cam_norm)
        axis_up = numpy.array([0.0, -1.0, 0.0]) if abs(self._cam_norm[1]) < abs(self._cam_norm[2]) else numpy.array([0.0, 0.0, 1.0])
        self._cam_axis_q = numpy.cross(self._cam_norm, axis_up)
        self._cam_axis_q /= numpy.linalg.norm(self._cam_axis_q)
        self._cam_axis_r = numpy.cross(self._cam_axis_q, self._cam_norm)
        self._cam_axis_r /= numpy.linalg.norm(self._cam_axis_r)

    def _createBrushPen(self) -> QPen:
        pen = QPen()
        pen.setWidth(self._brush_size)
        pen.setColor(Qt.GlobalColor.white)

        match self._brush_shape:
            case PaintTool.Brush.Shape.SQUARE:
                pen.setCapStyle(Qt.PenCapStyle.SquareCap)
            case PaintTool.Brush.Shape.CIRCLE:
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            case _:
                Logger.error(f"Unknown brush shape '{self._brush_shape}', painting may not work.")
        return pen

    def _createStrokeImage(self, polys: List[Polygon]) -> Tuple[QImage, Tuple[int, int]]:
        w, h = self._getPaintView().getUvTexDimensions()
        if w == 0 or h == 0 or len(polys) == 0:
            return QImage(w, h, QImage.Format.Format_RGB32), (0, 0)

        min_pt = numpy.array([numpy.inf, numpy.inf])
        max_pt = numpy.array([-numpy.inf, -numpy.inf])
        for poly in polys:
            for pt in poly:
                min_pt = numpy.minimum(min_pt, w * pt)
                max_pt = numpy.maximum(max_pt, h * pt)

        stroke_image = QImage(int(max_pt[0] - min_pt[0]) + 1, int(max_pt[1] - min_pt[1]) + 1, QImage.Format.Format_RGB32)
        stroke_image.fill(0)

        painter = QPainter(stroke_image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        path = QPainterPath()
        for poly in polys:
            path.moveTo(int(0.5 + w * poly[0][0] - min_pt[0]), int(0.5 + h * poly[0][1] - min_pt[1]))
            for pt in poly[1:]:
                path.lineTo(int(0.5 + w * pt[0] - min_pt[0]), int(0.5 + h * pt[1] - min_pt[1]))
        painter.fillPath(path, self._brush_pen.color())
        painter.end()

        return stroke_image, (int(min_pt[0] + 0.5), int(min_pt[1] + 0.5))

    def getPaintType(self) -> str:
        paint_view = self._getPaintView()
        if paint_view is None:
            return ""

        return paint_view.getPaintType()

    def setPaintType(self, paint_type: str) -> None:
        paint_view = self._getPaintView()
        if paint_view is None:
            return

        if paint_type != self.getPaintType():
            paint_view.setPaintType(paint_type)

            self._brush_pen = self._createBrushPen()
            self._updateScene()
            self.propertyChanged.emit()

    def getBrushSize(self) -> int:
        return self._brush_size

    def setBrushSize(self, brush_size: float) -> None:
        brush_size_int = int(brush_size)
        if brush_size_int != self._brush_size:
            self._brush_size = brush_size_int
            self._brush_pen = self._createBrushPen()
            self.propertyChanged.emit()

    def getBrushColor(self) -> str:
        return self._brush_color

    def setBrushColor(self, brush_color: str) -> None:
        if brush_color != self._brush_color:
            self._brush_color = brush_color
            self.propertyChanged.emit()

    def getBrushShape(self) -> int:
        return self._brush_shape

    def setBrushShape(self, brush_shape: int) -> None:
        if brush_shape != self._brush_shape:
            self._brush_shape = brush_shape
            self._brush_pen = self._createBrushPen()
            self.propertyChanged.emit()

    def getState(self) -> int:
        return self._state

    def undoStackAction(self, redo_instead: bool) -> bool:
        paint_view = self._getPaintView()
        if paint_view is None:
            return False

        if redo_instead:
            paint_view.redoStroke()
        else:
            paint_view.undoStroke()

        self._updateScene()
        return True

    def clear(self) -> None:
        paintview = self._getPaintView()
        if paintview is None:
            return

        width, height = paintview.getUvTexDimensions()
        clear_image = QImage(width, height, QImage.Format.Format_RGB32)
        clear_image.fill(Qt.GlobalColor.white)
        paintview.addStroke(clear_image, 0, 0, "none")

        self._updateScene()

    @staticmethod
    def _getPaintView() -> Optional[PaintView]:
        paint_view = Application.getInstance().getController().getActiveView()
        if paint_view is None or paint_view.getPluginId() != "PaintTool":
            return None
        return cast(PaintView, paint_view)

    @staticmethod
    def _getIntersectRatioViaPt(a: numpy.ndarray, pt: numpy.ndarray, b: numpy.ndarray, c: numpy.ndarray) -> float:
        """ Gets a single Barycentric coordinate of a point on a line segment.

        :param a: The start point of the line segment (one of the points of the triangle).
        :param pt: The point to find the Barycentric coordinate of (the one for point c, w.r.t. the ab line segment).
        :param b: The end point of the line segment (one of the points of the triangle).
        :param c: The third point of the triangle.
        :return: The Barycentric coordinate of pt, w.r.t. point c in the abc triangle, or 1.0 if outside that triangle.
        """

        # compute the intersection of (param) A - pt with (param) B - (param) C
        if (a == pt).all() or (b == c).all() or (a == c).all() or (a == b).all():
            return 1.0

        # force points to be 3d (and double-precision)
        def force3d(pt_: numpy.ndarray) -> numpy.ndarray:
            return pt_.astype(dtype=numpy.float64) if pt_.size >= 3 else numpy.array([pt_[0], pt_[1], 0.0], dtype=numpy.float64)
        a, pt, b, c = force3d(a), force3d(pt), force3d(b), force3d(c)

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

    @staticmethod
    def _remapBarycentric(triangle_a: Polygon, pt: numpy.ndarray, triangle_b: Polygon) -> numpy.ndarray:
        wa = PaintTool._getIntersectRatioViaPt(triangle_a[0], pt, triangle_a[1], triangle_a[2])
        wb = PaintTool._getIntersectRatioViaPt(triangle_a[1], pt, triangle_a[2], triangle_a[0])
        wc = PaintTool._getIntersectRatioViaPt(triangle_a[2], pt, triangle_a[0], triangle_a[1])
        wt = wa + wb + wc
        if wt == 0:
            return triangle_b[0]  # Shouldn't happen!
        return wa/wt * triangle_b[0] + wb/wt * triangle_b[1] + wc/wt * triangle_b[2]

    def _getStrokePolygon(self, size_adjust: float, stroke_a: numpy.ndarray, stroke_b: numpy.ndarray) -> Polygon:
        shape = None
        match self._brush_shape:
            case PaintTool.Brush.Shape.SQUARE:
                shape = Polygon.approximatedCircle(self._brush_size * size_adjust, 4)
            case PaintTool.Brush.Shape.CIRCLE:
                shape = Polygon.approximatedCircle(self._brush_size * size_adjust, 16)
            case _:
                Logger.error(f"Unknown brush shape '{self._brush_shape}'.")
        if shape is None:
            return Polygon()
        return shape.translate(stroke_a[0], stroke_a[1]).unionConvexHulls(shape.translate(stroke_b[0], stroke_b[1]))

    # NOTE: Currently, it's unclear how well this would work for non-convex brush-shapes.
    def _getUvAreasForStroke(self, face_id_a: int, face_id_b: int, world_coords_a: numpy.ndarray, world_coords_b: numpy.ndarray) -> List[Polygon]:
        """ Fetches all texture-coordinate areas within the provided stroke on the mesh.

        Calculates intersections of the stroke with the surface of the geometry and maps them to UV-space polygons.

        :param face_id_a: ID of the face where the stroke starts.
        :param face_id_b: ID of the face where the stroke ends.
        :param world_coords_a: 3D ('world') coordinates corresponding to the starting stroke point.
        :param world_coords_b: 3D ('world') coordinates corresponding to the ending stroke point.
        :return: A list of UV-mapped polygons representing areas intersected by the stroke on the node's mesh surface.
        """

        def get_projected_on_plane(pt: numpy.ndarray) -> numpy.ndarray:
            proj_pt = (pt - numpy.dot(self._cam_norm, pt - self._cam_pos) * self._cam_norm) - self._cam_pos
            y_coord = numpy.dot(self._cam_axis_r, proj_pt)
            x_coord = numpy.dot(self._cam_axis_q, proj_pt)
            return numpy.array([x_coord, y_coord])

        uv_a0, uv_a1, _ = self._node_cache.getMeshData().getFaceUvCoords(face_id_a)
        w_a0, w_a1, _ = self._mesh_transformed_cache.getFaceNodes(face_id_a)
        world_to_uv_size_factor = numpy.linalg.norm(uv_a1 - uv_a0) / numpy.linalg.norm(w_a1 - w_a0)

        stroke_poly = self._getStrokePolygon(
            world_to_uv_size_factor,
            get_projected_on_plane(world_coords_a),
            get_projected_on_plane(world_coords_b))

        candidates = set()
        candidates.add(face_id_a)
        candidates.add(face_id_b)

        res = []
        seen = set()
        while candidates:
            candidate = candidates.pop()
            if candidate in seen or candidate < 0:
                continue
            seen.add(candidate)

            _, fnorm = self._mesh_transformed_cache.getFacePlane(candidate)
            if numpy.dot(fnorm, self._cam_norm) < 0:  # <- facing away from the viewer
                continue

            va, vb, vc = self._mesh_transformed_cache.getFaceNodes(candidate)
            stroke_tri = Polygon([
                get_projected_on_plane(va),
                get_projected_on_plane(vb),
                get_projected_on_plane(vc)])
            face_uv_coordinates = self._node_cache.getMeshData().getFaceUvCoords(candidate)
            if face_uv_coordinates is None:
                continue
            ta, tb, tc = face_uv_coordinates
            original_uv_poly = Polygon([ta, tb, tc])
            uv_area = stroke_poly.intersection(stroke_tri).map(lambda pt: PaintTool._remapBarycentric(stroke_tri, pt, original_uv_poly))

            if not uv_area.isValid():
                continue
            res.append(uv_area)
            [candidates.add(x) for x in self._mesh_transformed_cache.getFaceNeighbourIDs(candidate)]
        return res

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
            return True

        if event.type == Event.ToolDeactivateEvent:
            return True

        if self._state != PaintTool.Paint.State.READY:
            return False

        if event.type == Event.MouseReleaseEvent and self._controller.getToolsEnabled():
            if MouseEvent.LeftButton not in cast(MouseEvent, event).buttons:
                return False
            self._mouse_held = False
            self._last_world_coords = None
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

            paintview = self._getPaintView()
            if paintview is None:
                return False

            if not self._faces_selection_pass:
                self._faces_selection_pass = CuraApplication.getInstance().getRenderer().getRenderPass("selection_faces")
                if not self._faces_selection_pass:
                    return False

            if not self._picking_pass:
                self._picking_pass = CuraApplication.getInstance().getRenderer().getRenderPass("picking_selected")
                if not self._picking_pass:
                    return False

            if self._camera is None:
                self._updateCamera()
            if self._camera is None:
                return False

            if node != self._node_cache:
                if self._node_cache is not None:
                    self._node_cache.transformationChanged.disconnect(self._nodeTransformChanged)
                self._node_cache = node
                self._node_cache.transformationChanged.connect(self._nodeTransformChanged)
                self._cache_dirty = True
            if self._cache_dirty:
                self._cache_dirty = False
                self._mesh_transformed_cache = self._node_cache.getMeshDataTransformed()
            if not self._mesh_transformed_cache:
                return False

            face_id = self._faces_selection_pass.getFaceIdAtPosition(mouse_evt.x, mouse_evt.y)
            if face_id < 0 or face_id >= self._mesh_transformed_cache.getFaceCount():
                return False
            world_coords = self._picking_pass.getPickedPosition(mouse_evt.x, mouse_evt.y).getData()

            if self._last_world_coords is None:
                self._last_world_coords = world_coords
                self._last_face_id = face_id

            uv_areas = self._getUvAreasForStroke(self._last_face_id, face_id, self._last_world_coords, world_coords)
            if len(uv_areas) == 0:
                return False
            stroke_img, (start_x, start_y) = self._createStrokeImage(uv_areas)
            paintview.addStroke(stroke_img, start_x, start_y, self._brush_color)

            self._last_world_coords = world_coords
            self._last_face_id = face_id
            self._updateScene(node)
            return True

        return False

    def getRequiredExtraRenderingPasses(self) -> list[str]:
        return ["selection_faces", "picking_selected"]

    @staticmethod
    def _updateScene(node: SceneNode = None):
        if node is None:
            node = Selection.getSelectedObject(0)
        if node is not None:
            Application.getInstance().getController().getScene().sceneChanged.emit(node)

    def _onSelectionChanged(self):
        super()._onSelectionChanged()

        self.setActiveView("PaintTool" if len(Selection.getAllSelectedObjects()) == 1 else None)
        self._updateState()

    def _updateState(self):
        if len(Selection.getAllSelectedObjects()) == 1 and self._controller.getActiveTool() == self:
            selected_object = Selection.getSelectedObject(0)
            if selected_object.callDecoration("getPaintTexture") is not None:
                new_state = PaintTool.Paint.State.READY
            else:
                new_state = PaintTool.Paint.State.PREPARING_MODEL
                self._prepare_texture_job = PrepareTextureJob(selected_object)
                self._prepare_texture_job.finished.connect(self._onPrepareTextureFinished)
                self._prepare_texture_job.start()
        else:
            new_state = PaintTool.Paint.State.MULTIPLE_SELECTION

        if new_state != self._state:
            self._state = new_state
            self.propertyChanged.emit()

    def _onPrepareTextureFinished(self, job: Job):
        if job == self._prepare_texture_job:
            self._prepare_texture_job = None
            self._state = PaintTool.Paint.State.READY
            self.propertyChanged.emit()

    def _updateIgnoreUnselectedObjects(self):
        ignore_unselected_objects = self._controller.getActiveView().name == "PaintTool"
        CuraApplication.getInstance().getRenderer().getRenderPass("selection").setIgnoreUnselectedObjects(ignore_unselected_objects)
        CuraApplication.getInstance().getRenderer().getRenderPass("selection_faces").setIgnoreUnselectedObjects(ignore_unselected_objects)
