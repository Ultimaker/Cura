# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.
import math

from collections import deque
from enum import IntEnum
import numpy
from PyQt6.QtCore import Qt, QObject, pyqtEnum, QPointF
from PyQt6.QtGui import QImage, QPainter, QPen, QBrush, QPolygonF, QPainterPath
from typing import cast, Optional, Tuple, List
import pyUvula as uvula

from UM.Application import Application
from UM.Event import Event, MouseEvent
from UM.Job import Job
from UM.Logger import Logger
from UM.Math.AxisAlignedBox2D import AxisAlignedBox2D
from UM.Math.Polygon import Polygon
from UM.Math.Vector import Vector
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
            FACE = 2

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
        self._view.currentPaintedObjectMeshDataChanged.connect(self._updateState)

        self._picking_pass: Optional[PickingPass] = None
        self._faces_selection_pass: Optional[SelectionPass] = None

        self._shortcut_key: Qt.Key = Qt.Key.Key_P

        self._node_cache: Optional[SceneNode] = None
        self._mesh_transformed_cache: Optional[MeshData] = None
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
        self._controller.activeStageChanged.connect(self._updateActiveView)

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

    def _createStrokePath(self, polygons: List[Polygon]) -> QPainterPath:
        path = QPainterPath()

        for polygon in polygons:
            path.moveTo(polygon[0][0], polygon[0][1])
            for point in polygon:
                path.lineTo(point[0], point[1])
            path.closeSubpath()

        return path

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
        self._updateScene(update_node = True)

    def redoStackAction(self) -> None:
        self._view.redoStroke()
        self._updateScene(update_node = True)

    def clear(self) -> None:
        self._view.clearPaint()
        self._updateScene(update_node = True)

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

    # NOTE: Currently, it's unclear how well this would work for non-convex brush-shapes.
    def _getUvAreasForStroke(self, world_coords_a: numpy.ndarray, world_coords_b: numpy.ndarray, face_id: int) -> List[Polygon]:
        """ Fetches all texture-coordinate areas within the provided stroke on the mesh.

        Calculates intersections of the stroke with the surface of the geometry and maps them to UV-space polygons.

        :param world_coords_a: 3D ('world') coordinates corresponding to the starting stroke point.
        :param world_coords_b: 3D ('world') coordinates corresponding to the ending stroke point.
        :param face_id: the ID of the face at the center of the stroke
        :return: A list of UV-mapped polygons representing areas intersected by the stroke on the node's mesh surface.
        """

        def get_projected_on_plane(pt: numpy.ndarray) -> numpy.ndarray:
            return numpy.array([*self._camera.projectToViewport(Vector(*pt))], dtype=numpy.float32)

        stroke_poly = self._getStrokePolygon(get_projected_on_plane(world_coords_a), get_projected_on_plane(world_coords_b))
        stroke_poly.toType(numpy.float32)

        mesh_indices = self._mesh_transformed_cache.getIndices()
        if mesh_indices is None:
            mesh_indices = numpy.array([], dtype=numpy.int32)

        res = uvula.project(stroke_poly.getPoints(),
                            self._mesh_transformed_cache.getVertices(),
                            mesh_indices,
                            self._node_cache.getMeshData().getUVCoordinates(),
                            self._node_cache.getMeshData().getFacesConnections(),
                            self._view.getUvTexDimensions()[0],
                            self._view.getUvTexDimensions()[1],
                            self._camera.getProjectToViewMatrix().getData(),
                            self._camera.isPerspective(),
                            self._camera.getViewportWidth(),
                            self._camera.getViewportHeight(),
                            self._cam_norm,
                            face_id)
        return [Polygon(points) for points in res]

    def _getCoplanarConnectedFaces(self, face_id: int, angle_threshold: float = 0.99) -> List[int]:
        """Find all connected faces that are coplanar (or nearly coplanar) with the given face.
        
        This allows painting of "visual faces" - all triangles that form a flat surface together.
        Uses BFS with deque for efficient face traversal.
        
        :param face_id: The starting face ID
        :param angle_threshold: Cosine of the maximum angle difference (0.99 ≈ 8 degrees)
        :return: List of all connected coplanar face IDs including the starting face
        """
        mesh_data = self._mesh_transformed_cache
        original_mesh_data = self._node_cache.getMeshData()
        
        if mesh_data is None or face_id < 0 or face_id >= mesh_data.getFaceCount():
            return [face_id]
        
        # Get the normal of the starting face
        try:
            _, start_normal = mesh_data.getFacePlane(face_id)
            start_normal = start_normal / numpy.linalg.norm(start_normal)
        except:
            return [face_id]
        
        # BFS using deque for O(1) popleft
        visited = set()
        to_visit = deque([face_id])
        coplanar_faces = []
        
        while to_visit:
            current_face = to_visit.popleft()
            
            if current_face in visited or current_face < 0:
                continue
            
            visited.add(current_face)
            
            # Check if this face is coplanar with the start face
            try:
                _, current_normal = mesh_data.getFacePlane(current_face)
                current_normal = current_normal / numpy.linalg.norm(current_normal)
                
                # Calculate dot product (cosine of angle between normals)
                dot_product = abs(numpy.dot(start_normal, current_normal))
                
                if dot_product >= angle_threshold:
                    coplanar_faces.append(current_face)
                    
                    # Add unvisited neighbors to the queue
                    neighbors = original_mesh_data.getFaceNeighbourIDs(current_face)
                    to_visit.extend(n for n in neighbors if n >= 0 and n not in visited)
            except:
                continue
        
        return coplanar_faces if coplanar_faces else [face_id]

    def _getUvAreasForFace(self, face_id: int) -> List[Polygon]:
        """Get UV polygon(s) for an entire face.
        
        In face mode, this gets all connected coplanar triangles that form a "visual face".
        The brush size controls the angle threshold: smaller brush = stricter coplanarity check.

        :param face_id: the ID of the face to get UV areas for
        :return: A list of UV-mapped polygons representing the entire face
        """
        mesh_data = self._node_cache.getMeshData()
        
        if not mesh_data.hasUVCoordinates():
            return []
        
        # Map brush size (1-100) to angle threshold (0.999-0.90)
        # Smaller brush = stricter angle (only very coplanar faces)
        # Larger brush = looser angle (more faces included)
        angle_threshold = 0.999 - (self._brush_size / 100.0) * 0.099
        
        # Get all coplanar connected faces
        coplanar_faces = self._getCoplanarConnectedFaces(face_id, angle_threshold)
        
        # Batch process UV polygons using list comprehension
        tex_width, tex_height = self._view.getUvTexDimensions()
        
        uv_polygons = []
        for face in coplanar_faces:
            uv_coords = mesh_data.getFaceUvCoords(face)
            if uv_coords is not None:
                uv_a, uv_b, uv_c = uv_coords
                uv_polygon_points = numpy.array([uv_a, uv_b, uv_c], dtype=numpy.float32)
                uv_polygon_points[:, 0] *= tex_width
                uv_polygon_points[:, 1] *= tex_height
                uv_polygons.append(Polygon(uv_polygon_points))
        
        return uv_polygons

    def event(self, event: Event) -> bool:
        """Handle mouse and keyboard events.

        :param event: The event to handle.
        :return: Whether this event has been caught by this tool (True) or should
        be passed on (False).
        """
        super().event(event)

        painted_object = self._view.getPaintedObject()
        if painted_object is None:
            return False

        # Make sure the displayed values are updated if the bounding box of the selected mesh(es) changes
        if event.type == Event.ToolActivateEvent:
            return True

        if event.type == Event.ToolDeactivateEvent:
            return True

        if self._state != PaintTool.Paint.State.READY:
            return False

        if self._controller.getActiveView() is not self._view:
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

            if painted_object != self._node_cache:
                if self._node_cache is not None:
                    self._node_cache.transformationChanged.disconnect(self._nodeTransformChanged)
                self._node_cache = painted_object
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
                    self._updateScene(painted_object, update_node = self._mouse_held)
                    return True
                return False

            world_coords_vec = self._picking_pass.getPickedPosition(mouse_evt.x, mouse_evt.y)
            world_coords = world_coords_vec.getData()
            if self._last_world_coords is None:
                self._last_world_coords = world_coords

            event_caught = False # Propagate mouse event if only moving the cursor, not to block e.g. rotation
            try:
                brush_color = self._brush_color if self.getPaintType() != "extruder" else str(self._brush_extruder)
                
                # In face mode, paint/preview the entire face
                if self._brush_shape == PaintTool.Brush.Shape.FACE:
                    uv_areas_cursor = self._getUvAreasForFace(face_id)
                else:
                    uv_areas_cursor = self._getUvAreasForStroke(world_coords, world_coords, face_id)
                
                if len(uv_areas_cursor) > 0:
                    cursor_path = self._createStrokePath(uv_areas_cursor)
                    self._view.setCursorStroke(cursor_path, brush_color)
                else:
                    self._view.clearCursorStroke()

                if self._mouse_held:
                    # In face mode, paint the entire face
                    if self._brush_shape == PaintTool.Brush.Shape.FACE:
                        uv_areas = self._getUvAreasForFace(face_id)
                    else:
                        uv_areas = self._getUvAreasForStroke(self._last_world_coords, world_coords, face_id)
                    
                    if len(uv_areas) == 0:
                        return False
                    event_caught = True
                    self._view.addStroke(uv_areas, brush_color, is_moved)
            except:
                Logger.logException("e", "Error when adding paint stroke")

            self._last_world_coords = world_coords
            self._updateScene(painted_object, update_node = event_caught)
            return event_caught

        return False

    def getRequiredExtraRenderingPasses(self) -> list[str]:
        return ["selection_faces", "picking_selected"]

    def _updateScene(self, node: SceneNode = None, update_node: bool = False):
        """
        Updates the current displayed scene
        :param node: the specific scene node to be updated, otherwise the current painted object will be used
        :param update_node: Indicates whether the specific node should be updated, which will invalidate its slicing
                            data, or the whole scene, which will just trigger a redraw of the view
        :return:
        """
        if node is None:
            node = self._view.getPaintedObject()
        if node is not None:
            if update_node:
                Application.getInstance().getController().getScene().sceneChanged.emit(node)
            else:
                scene = self.getController().getScene()
                scene.sceneChanged.emit(scene.getRoot())

    def _onSelectionChanged(self) -> None:
        super()._onSelectionChanged()

        single_selection = len(Selection.getAllSelectedObjects()) == 1
        self._view.setPaintedObject(Selection.getSelectedObject(0) if single_selection else None)
        self._updateActiveView()
        self._updateState()

    def _updateActiveView(self) -> None:
        has_painted_object = self._view.hasPaintedObject()
        stage_is_prepare = self._controller.getActiveStage().stageId == "PrepareStage"
        self.setActiveView("PaintTool" if has_painted_object and stage_is_prepare else None)

    def _updateState(self):
        painted_object = self._view.getPaintedObject()
        if painted_object is not None and self._controller.getActiveTool() == self:
            if painted_object.callDecoration("getPaintTexture") is not None and painted_object.getMeshData().hasUVCoordinates():
                new_state = PaintTool.Paint.State.READY
            else:
                new_state = PaintTool.Paint.State.PREPARING_MODEL
                self._prepare_texture_job = PrepareTextureJob(painted_object)
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
            self._updateScene()

    def _updateIgnoreUnselectedObjects(self):
        ignore_unselected_objects = self._controller.getActiveView().name == "PaintTool"
        CuraApplication.getInstance().getRenderer().getRenderPass("selection").setIgnoreUnselectedObjects(ignore_unselected_objects)
        CuraApplication.getInstance().getRenderer().getRenderPass("selection_faces").setIgnoreUnselectedObjects(ignore_unselected_objects)
