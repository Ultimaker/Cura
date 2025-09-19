# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.
import math

from enum import IntEnum
import numpy
from PyQt6.QtCore import Qt, QObject, pyqtEnum, QPointF
from PyQt6.QtGui import QImage, QPainter, QPen, QBrush, QPolygonF
from typing import cast, Optional, Tuple, List

from UM.Application import Application
from UM.Event import Event, MouseEvent
from UM.Job import Job
from UM.Logger import Logger
from UM.Math.AxisAlignedBox2D import AxisAlignedBox2D
from UM.Math.Polygon import Polygon
from UM.Math.Vector import Vector
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

    def __init__(self, view: PaintView) -> None:
        super().__init__()

        self._view: PaintView = view
        self._view.canUndoChanged.connect(self._onCanUndoChanged)
        self._view.canRedoChanged.connect(self._onCanRedoChanged)

        self._picking_pass: Optional[PickingPass] = None
        self._faces_selection_pass: Optional[SelectionPass] = None

        self._shortcut_key: Qt.Key = Qt.Key.Key_P

        self._node_cache: Optional[SceneNode] = None
        self._mesh_transformed_cache = None
        self._cache_dirty: bool = True

        self._brush_size: int = 10
        self._brush_color: str = "preferred"
        self._brush_extruder: int = 0
        self._brush_shape: PaintTool.Brush.Shape = PaintTool.Brush.Shape.CIRCLE
        self._brush_pen: QPen = self._createBrushPen()

        self._mouse_held: bool = False

        self._last_world_coords: Optional[numpy.ndarray] = None

        self._state: PaintTool.Paint.State = PaintTool.Paint.State.MULTIPLE_SELECTION
        self._prepare_texture_job: Optional[PrepareTextureJob] = None

        self.setExposedProperties("PaintType", "BrushSize", "BrushColor", "BrushShape", "BrushExtruder", "State", "CanUndo", "CanRedo")

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
        pen.setWidth(2)
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
        return PaintTool._rasterizePolygons(polys, self._brush_pen, QBrush(self._brush_pen.color()))

    def getPaintType(self) -> str:
        return self._view.getPaintType()

    def setPaintType(self, paint_type: str) -> None:
        if paint_type != self.getPaintType():
            self._view.setPaintType(paint_type)

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

    def getBrushExtruder(self) -> int:
        return self._brush_extruder

    def setBrushExtruder(self, brush_extruder: int) -> None:
        if brush_extruder != self._brush_extruder:
            self._brush_extruder = brush_extruder
            self.propertyChanged.emit()

    def getBrushShape(self) -> int:
        return self._brush_shape

    def setBrushShape(self, brush_shape: int) -> None:
        if brush_shape != self._brush_shape:
            self._brush_shape = brush_shape
            self._brush_pen = self._createBrushPen()
            self.propertyChanged.emit()

    def getCanUndo(self) -> bool:
        return self._view.canUndo()

    def getCanRedo(self) -> bool:
        return self._view.canRedo()

    def getState(self) -> int:
        return self._state

    def _onCanUndoChanged(self):
        self.propertyChanged.emit()

    def _onCanRedoChanged(self):
        self.propertyChanged.emit()

    def undoStackAction(self) -> None:
        self._view.undoStroke()
        self._updateScene()

    def redoStackAction(self) -> None:
        self._view.redoStroke()
        self._updateScene()

    def clear(self) -> None:
        width, height = self._view.getUvTexDimensions()
        clear_image = QImage(width, height, QImage.Format.Format_RGB32)
        clear_image.fill(Qt.GlobalColor.white)
        self._view.addStroke(clear_image, 0, 0, "none" if self.getPaintType() != "extruder" else "0", False)

        self._updateScene()

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

    @staticmethod
    def _getBarycentricCoordinates(points: numpy.array, triangle: numpy.array) -> Optional[numpy.array]:
        v0 = triangle[1] - triangle[0]
        v1 = triangle[2] - triangle[0]
        v2 = points - triangle[0]

        d00 = numpy.sum(v0 * v0, axis=0)
        d01 = numpy.sum(v0 * v1, axis=0)
        d11 = numpy.sum(v1 * v1, axis=0)
        d20 = numpy.sum(v2 * v0, axis=1)
        d21 = numpy.sum(v2 * v1, axis=1)

        denominator = d00 * d11 - d01 ** 2

        if denominator < 1e-6:  # Degenerate triangle
            return None

        v = (d11 * d20 - d01 * d21) / denominator
        w = (d00 * d21 - d01 * d20) / denominator
        u = 1 - v - w

        return numpy.column_stack((u, v, w))

    def _getStrokePolygon(self, stroke_a: numpy.ndarray, stroke_b: numpy.ndarray) -> Polygon:
        shape = None
        side = self._brush_size
        match self._brush_shape:
            case PaintTool.Brush.Shape.SQUARE:
                shape = Polygon([(side, side), (-side, side), (-side, -side), (side, -side)])
            case PaintTool.Brush.Shape.CIRCLE:
                shape = Polygon.approximatedCircle(side, 32)
            case _:
                Logger.error(f"Unknown brush shape '{self._brush_shape}'.")
        if shape is None:
            return Polygon()
        return shape.translate(stroke_a[0], stroke_a[1]).unionConvexHulls(shape.translate(stroke_b[0], stroke_b[1]))

    @staticmethod
    def _rasterizePolygons(polygons: List[Polygon], pen: QPen, brush: QBrush) -> Tuple[QImage, Tuple[int, int]]:
        if not polygons:
            return QImage(), (0, 0)

        bounding_box = polygons[0].getBoundingBox()
        for polygon in polygons[1:]:
            bounding_box += polygon.getBoundingBox()

        bounding_box = AxisAlignedBox2D(numpy.array([math.floor(bounding_box.left), math.floor(bounding_box.top)]),
                                        numpy.array([math.ceil(bounding_box.right), math.ceil(bounding_box.bottom)]))

        # Use RGB32 which is more optimized for drawing to
        image = QImage(int(bounding_box.width), int(bounding_box.height), QImage.Format.Format_RGB32)
        image.fill(0)

        painter = QPainter(image)
        painter.translate(-bounding_box.left, -bounding_box.bottom)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setPen(pen)
        painter.setBrush(brush)

        for polygon in polygons:
            painter.drawPolygon(QPolygonF([QPointF(point[0], point[1]) for point in polygon]))

        painter.end()

        return image, (int(bounding_box.left), int(bounding_box.bottom))

    # NOTE: Currently, it's unclear how well this would work for non-convex brush-shapes.
    def _getUvAreasForStroke(self, world_coords_a: numpy.ndarray, world_coords_b: numpy.ndarray) -> List[Polygon]:
        """ Fetches all texture-coordinate areas within the provided stroke on the mesh.

        Calculates intersections of the stroke with the surface of the geometry and maps them to UV-space polygons.

        :param face_id_a: ID of the face where the stroke starts.
        :param face_id_b: ID of the face where the stroke ends.
        :param world_coords_a: 3D ('world') coordinates corresponding to the starting stroke point.
        :param world_coords_b: 3D ('world') coordinates corresponding to the ending stroke point.
        :return: A list of UV-mapped polygons representing areas intersected by the stroke on the node's mesh surface.
        """

        def get_projected_on_plane(pt: numpy.ndarray) -> numpy.ndarray:
            return numpy.array([*self._camera.projectToViewport(Vector(*pt))], dtype=numpy.float32)

        def get_projected_on_viewport_image(pt: numpy) -> numpy.ndarray:
            return numpy.array([pt[0] + self._camera.getViewportWidth() / 2.0,
                                self._camera.getViewportHeight() - (pt[1] + self._camera.getViewportHeight() / 2.0)],
                               dtype=numpy.float32)

        stroke_poly = self._getStrokePolygon(get_projected_on_plane(world_coords_a), get_projected_on_plane(world_coords_b))
        stroke_poly_viewport = Polygon([get_projected_on_viewport_image(point) for point in stroke_poly])

        faces_image, (faces_x, faces_y) = PaintTool._rasterizePolygons([stroke_poly_viewport],
                                                                       QPen(Qt.PenStyle.NoPen),
                                                                       QBrush(Qt.GlobalColor.white))
        faces = self._faces_selection_pass.getFacesIdsUnderMask(faces_image, faces_x, faces_y)

        texture_dimensions = numpy.array(list(self._view.getUvTexDimensions()))

        res = []
        for face in faces:
            _, fnorm = self._mesh_transformed_cache.getFacePlane(face)
            if numpy.dot(fnorm, self._cam_norm) < 0:  # <- facing away from the viewer
                continue

            va, vb, vc = self._mesh_transformed_cache.getFaceNodes(face)
            stroke_tri = Polygon([
                get_projected_on_plane(va),
                get_projected_on_plane(vb),
                get_projected_on_plane(vc)])
            face_uv_coordinates = self._node_cache.getMeshData().getFaceUvCoords(face)
            if face_uv_coordinates is None:
                continue
            ta, tb, tc = face_uv_coordinates
            original_uv_poly = numpy.array([ta, tb, tc])
            uv_area = stroke_poly.intersection(stroke_tri)

            if uv_area.isValid():
                uv_area_barycentric = PaintTool._getBarycentricCoordinates(uv_area.getPoints(), stroke_tri.getPoints())
                if uv_area_barycentric is not None:
                    res.append(Polygon((uv_area_barycentric @ original_uv_poly) * texture_dimensions))

        return res

    def event(self, event: Event) -> bool:
        """Handle mouse and keyboard events.

        :param event: The event to handle.
        :return: Whether this event has been caught by this tool (True) or should
        be passed on (False).
        """
        super().event(event)

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
            return True

        is_moved = event.type == Event.MouseMoveEvent
        is_pressed = event.type == Event.MousePressEvent
        if (is_moved or is_pressed) and self._controller.getToolsEnabled():
            mouse_evt = cast(MouseEvent, event)

            if not self._picking_pass:
                self._picking_pass = CuraApplication.getInstance().getRenderer().getRenderPass("picking_selected")
                if not self._picking_pass:
                    return False

            if is_pressed:
                if MouseEvent.LeftButton not in mouse_evt.buttons:
                    return False
                else:
                    self._mouse_held = True

            if not self._faces_selection_pass:
                self._faces_selection_pass = CuraApplication.getInstance().getRenderer().getRenderPass("selection_faces")
                if not self._faces_selection_pass:
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
                if self._view.clearCursorStroke():
                    self._updateScene(node)
                    return True
                return False

            world_coords_vec = self._picking_pass.getPickedPosition(mouse_evt.x, mouse_evt.y)
            world_coords = world_coords_vec.getData()
            if self._last_world_coords is None:
                self._last_world_coords = world_coords

            try:
                brush_color = self._brush_color if self.getPaintType() != "extruder" else str(self._brush_extruder)
                uv_areas_cursor = self._getUvAreasForStroke(world_coords, world_coords)
                if len(uv_areas_cursor) > 0:
                    cursor_stroke_img, (start_x, start_y) = self._createStrokeImage(uv_areas_cursor)
                    self._view.setCursorStroke(cursor_stroke_img, start_x, start_y, brush_color)
                else:
                    self._view.clearCursorStroke()

                if self._mouse_held:
                    uv_areas = self._getUvAreasForStroke(self._last_world_coords, world_coords)
                    if len(uv_areas) == 0:
                        return False
                    stroke_img, (start_x, start_y) = self._createStrokeImage(uv_areas)
                    self._view.addStroke(stroke_img, start_x, start_y, brush_color, is_moved)
            except:
                Logger.logException("e", "Error when adding paint stroke")

            self._last_world_coords = world_coords
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
