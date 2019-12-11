# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from UM.Mesh.MeshData import MeshData
from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.Settings.ExtruderManager import ExtruderManager
from UM.Application import Application #To modify the maximum zoom level.
from UM.i18n import i18nCatalog
from UM.Scene.Platform import Platform
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Resources import Resources
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Math.Vector import Vector
from UM.Math.Matrix import Matrix
from UM.Math.Color import Color
from UM.Math.AxisAlignedBox import AxisAlignedBox
from UM.Math.Polygon import Polygon
from UM.Message import Message
from UM.Signal import Signal
from PyQt5.QtCore import QTimer
from UM.View.RenderBatch import RenderBatch
from UM.View.GL.OpenGL import OpenGL
from cura.Settings.GlobalStack import GlobalStack

catalog = i18nCatalog("cura")

import numpy
import math

from typing import List, Optional, TYPE_CHECKING, Any, Set, cast, Iterable, Dict

if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication
    from cura.Settings.ExtruderStack import ExtruderStack
    from UM.Settings.ContainerStack import ContainerStack

# Radius of disallowed area in mm around prime. I.e. how much distance to keep from prime position.
PRIME_CLEARANCE = 6.5


##  Build volume is a special kind of node that is responsible for rendering the printable area & disallowed areas.
class BuildVolume(SceneNode):
    raftThicknessChanged = Signal()

    def __init__(self, application: "CuraApplication", parent: Optional[SceneNode] = None) -> None:
        super().__init__(parent)
        self._application = application
        self._machine_manager = self._application.getMachineManager()

        self._volume_outline_color = None  # type: Optional[Color]
        self._x_axis_color = None  # type: Optional[Color]
        self._y_axis_color = None  # type: Optional[Color]
        self._z_axis_color = None  # type: Optional[Color]
        self._disallowed_area_color = None  # type: Optional[Color]
        self._error_area_color = None  # type: Optional[Color]

        self._width = 0  # type: float
        self._height = 0  # type: float
        self._depth = 0  # type: float
        self._shape = ""  # type: str

        self._shader = None

        self._origin_mesh = None  # type: Optional[MeshData]
        self._origin_line_length = 20
        self._origin_line_width = 1.5
        self._enabled = False

        self._grid_mesh = None   # type: Optional[MeshData]
        self._grid_shader = None

        self._disallowed_areas = []  # type: List[Polygon]
        self._disallowed_areas_no_brim = []  # type: List[Polygon]
        self._disallowed_area_mesh = None  # type: Optional[MeshData]
        self._disallowed_area_size = 0.

        self._error_areas = []  # type: List[Polygon]
        self._error_mesh = None  # type: Optional[MeshData]

        self.setCalculateBoundingBox(False)
        self._volume_aabb = None  # type: Optional[AxisAlignedBox]

        self._raft_thickness = 0.0
        self._extra_z_clearance = 0.0
        self._adhesion_type = None  # type: Any
        self._platform = Platform(self)

        self._build_volume_message = Message(catalog.i18nc("@info:status",
            "The build volume height has been reduced due to the value of the"
            " \"Print Sequence\" setting to prevent the gantry from colliding"
            " with printed models."), title = catalog.i18nc("@info:title", "Build Volume"))

        self._global_container_stack = None  # type: Optional[GlobalStack]

        self._stack_change_timer = QTimer()
        self._stack_change_timer.setInterval(100)
        self._stack_change_timer.setSingleShot(True)
        self._stack_change_timer.timeout.connect(self._onStackChangeTimerFinished)

        self._application.globalContainerStackChanged.connect(self._onStackChanged)

        self._onStackChanged()

        self._engine_ready = False
        self._application.engineCreatedSignal.connect(self._onEngineCreated)

        self._has_errors = False
        self._application.getController().getScene().sceneChanged.connect(self._onSceneChanged)

        #Objects loaded at the moment. We are connected to the property changed events of these objects.
        self._scene_objects = set()  # type: Set[SceneNode]

        self._scene_change_timer = QTimer()
        self._scene_change_timer.setInterval(100)
        self._scene_change_timer.setSingleShot(True)
        self._scene_change_timer.timeout.connect(self._onSceneChangeTimerFinished)

        self._setting_change_timer = QTimer()
        self._setting_change_timer.setInterval(150)
        self._setting_change_timer.setSingleShot(True)
        self._setting_change_timer.timeout.connect(self._onSettingChangeTimerFinished)

        # Must be after setting _build_volume_message, apparently that is used in getMachineManager.
        # activeQualityChanged is always emitted after setActiveVariant, setActiveMaterial and setActiveQuality.
        # Therefore this works.
        self._machine_manager.activeQualityChanged.connect(self._onStackChanged)

        # Enable and disable extruder
        self._machine_manager.extruderChanged.connect(self.updateNodeBoundaryCheck)

        # List of settings which were updated
        self._changed_settings_since_last_rebuild = []  # type: List[str]

    def _onSceneChanged(self, source):
        if self._global_container_stack:
            # Ignore anything that is not something we can slice in the first place!
            if source.callDecoration("isSliceable"):
                self._scene_change_timer.start()

    def _onSceneChangeTimerFinished(self):
        root = self._application.getController().getScene().getRoot()
        new_scene_objects = set(node for node in BreadthFirstIterator(root) if node.callDecoration("isSliceable"))
        if new_scene_objects != self._scene_objects:
            for node in new_scene_objects - self._scene_objects: #Nodes that were added to the scene.
                self._updateNodeListeners(node)
                node.decoratorsChanged.connect(self._updateNodeListeners)  # Make sure that decoration changes afterwards also receive the same treatment
            for node in self._scene_objects - new_scene_objects: #Nodes that were removed from the scene.
                per_mesh_stack = node.callDecoration("getStack")
                if per_mesh_stack:
                    per_mesh_stack.propertyChanged.disconnect(self._onSettingPropertyChanged)
                active_extruder_changed = node.callDecoration("getActiveExtruderChangedSignal")
                if active_extruder_changed is not None:
                    node.callDecoration("getActiveExtruderChangedSignal").disconnect(self._updateDisallowedAreasAndRebuild)
                node.decoratorsChanged.disconnect(self._updateNodeListeners)
            self.rebuild()

            self._scene_objects = new_scene_objects
            self._onSettingPropertyChanged("print_sequence", "value")  # Create fake event, so right settings are triggered.

    ##  Updates the listeners that listen for changes in per-mesh stacks.
    #
    #   \param node The node for which the decorators changed.
    def _updateNodeListeners(self, node: SceneNode):
        per_mesh_stack = node.callDecoration("getStack")
        if per_mesh_stack:
            per_mesh_stack.propertyChanged.connect(self._onSettingPropertyChanged)
        active_extruder_changed = node.callDecoration("getActiveExtruderChangedSignal")
        if active_extruder_changed is not None:
            active_extruder_changed.connect(self._updateDisallowedAreasAndRebuild)

    def setWidth(self, width: float) -> None:
        self._width = width

    def setHeight(self, height: float) -> None:
        self._height = height

    def setDepth(self, depth: float) -> None:
        self._depth = depth

    def setShape(self, shape: str) -> None:
        if shape:
            self._shape = shape

    ##  Get the length of the 3D diagonal through the build volume.
    #
    #   This gives a sense of the scale of the build volume in general.
    def getDiagonalSize(self) -> float:
        return math.sqrt(self._width * self._width + self._height * self._height + self._depth * self._depth)

    def getDisallowedAreas(self) -> List[Polygon]:
        return self._disallowed_areas

    def getDisallowedAreasNoBrim(self) -> List[Polygon]:
        return self._disallowed_areas_no_brim

    def setDisallowedAreas(self, areas: List[Polygon]):
        self._disallowed_areas = areas

    def render(self, renderer):
        if not self.getMeshData() or not self.isVisible():
            return True

        if not self._shader:
            self._shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "default.shader"))
            self._grid_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "grid.shader"))
            theme = self._application.getTheme()
            self._grid_shader.setUniformValue("u_plateColor", Color(*theme.getColor("buildplate").getRgb()))
            self._grid_shader.setUniformValue("u_gridColor0", Color(*theme.getColor("buildplate_grid").getRgb()))
            self._grid_shader.setUniformValue("u_gridColor1", Color(*theme.getColor("buildplate_grid_minor").getRgb()))

        renderer.queueNode(self, mode = RenderBatch.RenderMode.Lines)
        renderer.queueNode(self, mesh = self._origin_mesh, backface_cull = True)
        renderer.queueNode(self, mesh = self._grid_mesh, shader = self._grid_shader, backface_cull = True)
        if self._disallowed_area_mesh:
            renderer.queueNode(self, mesh = self._disallowed_area_mesh, shader = self._shader, transparent = True, backface_cull = True, sort = -9)

        if self._error_mesh:
            renderer.queueNode(self, mesh=self._error_mesh, shader=self._shader, transparent=True,
                               backface_cull=True, sort=-8)

        return True

    ##  For every sliceable node, update node._outside_buildarea
    #
    def updateNodeBoundaryCheck(self):
        if not self._global_container_stack:
            return

        root = self._application.getController().getScene().getRoot()
        nodes = cast(List[SceneNode], list(cast(Iterable, BreadthFirstIterator(root))))
        group_nodes = []  # type: List[SceneNode]

        build_volume_bounding_box = self.getBoundingBox()
        if build_volume_bounding_box:
            # It's over 9000!
            # We set this to a very low number, as we do allow models to intersect the build plate.
            # This means the model gets cut off at the build plate.
            build_volume_bounding_box = build_volume_bounding_box.set(bottom=-9001)
        else:
            # No bounding box. This is triggered when running Cura from command line with a model for the first time
            # In that situation there is a model, but no machine (and therefore no build volume.
            return

        for node in nodes:
            # Need to check group nodes later
            if node.callDecoration("isGroup"):
                group_nodes.append(node)  # Keep list of affected group_nodes

            if node.callDecoration("isSliceable") or node.callDecoration("isGroup"):
                if not isinstance(node, CuraSceneNode):
                    continue

                if node.collidesWithBbox(build_volume_bounding_box):
                    node.setOutsideBuildArea(True)
                    continue

                if node.collidesWithAreas(self.getDisallowedAreas()):
                    node.setOutsideBuildArea(True)
                    continue
                # If the entire node is below the build plate, still mark it as outside.
                node_bounding_box = node.getBoundingBox()
                if node_bounding_box and node_bounding_box.top < 0:
                    node.setOutsideBuildArea(True)
                    continue
                # Mark the node as outside build volume if the set extruder is disabled
                extruder_position = node.callDecoration("getActiveExtruderPosition")
                try:
                    if not self._global_container_stack.extruderList[int(extruder_position)].isEnabled:
                        node.setOutsideBuildArea(True)
                        continue
                except IndexError:
                    continue

                node.setOutsideBuildArea(False)

        # Group nodes should override the _outside_buildarea property of their children.
        for group_node in group_nodes:
            children = group_node.getAllChildren()

            # Check if one or more children are non-printable and if so, set the parent as non-printable:
            for child_node in children:
                if child_node.isOutsideBuildArea():
                    group_node.setOutsideBuildArea(True)
                    break

            # Apply results of the check to all children of the group:
            for child_node in children:
                child_node.setOutsideBuildArea(group_node.isOutsideBuildArea())

    ##  Update the outsideBuildArea of a single node, given bounds or current build volume
    def checkBoundsAndUpdate(self, node: CuraSceneNode, bounds: Optional[AxisAlignedBox] = None) -> None:
        if not isinstance(node, CuraSceneNode) or self._global_container_stack is None:
            return

        if bounds is None:
            build_volume_bounding_box = self.getBoundingBox()
            if build_volume_bounding_box:
                # It's over 9000!
                build_volume_bounding_box = build_volume_bounding_box.set(bottom=-9001)
            else:
                # No bounding box. This is triggered when running Cura from command line with a model for the first time
                # In that situation there is a model, but no machine (and therefore no build volume.
                return
        else:
            build_volume_bounding_box = bounds

        if node.callDecoration("isSliceable") or node.callDecoration("isGroup"):
            if node.collidesWithBbox(build_volume_bounding_box):
                node.setOutsideBuildArea(True)
                return

            if node.collidesWithAreas(self.getDisallowedAreas()):
                node.setOutsideBuildArea(True)
                return

            # Mark the node as outside build volume if the set extruder is disabled
            extruder_position = node.callDecoration("getActiveExtruderPosition")
            if not self._global_container_stack.extruderList[int(extruder_position)].isEnabled:
                node.setOutsideBuildArea(True)
                return

            node.setOutsideBuildArea(False)

    def _buildGridMesh(self, min_w: float, max_w: float, min_h: float, max_h: float, min_d: float, max_d:float, z_fight_distance: float) -> MeshData:
        mb = MeshBuilder()
        if self._shape != "elliptic":
            # Build plate grid mesh
            mb.addQuad(
                Vector(min_w, min_h - z_fight_distance, min_d),
                Vector(max_w, min_h - z_fight_distance, min_d),
                Vector(max_w, min_h - z_fight_distance, max_d),
                Vector(min_w, min_h - z_fight_distance, max_d)
            )

            for n in range(0, 6):
                v = mb.getVertex(n)
                mb.setVertexUVCoordinates(n, v[0], v[2])
            return mb.build()
        else:
            aspect = 1.0
            scale_matrix = Matrix()
            if self._width != 0:
                # Scale circular meshes by aspect ratio if width != height
                aspect = self._depth / self._width
                scale_matrix.compose(scale=Vector(1, 1, aspect))
            mb.addVertex(0, min_h - z_fight_distance, 0)
            mb.addArc(max_w, Vector.Unit_Y, center=Vector(0, min_h - z_fight_distance, 0))
            sections = mb.getVertexCount() - 1  # Center point is not an arc section
            indices = []
            for n in range(0, sections - 1):
                indices.append([0, n + 2, n + 1])
            mb.addIndices(numpy.asarray(indices, dtype=numpy.int32))
            mb.calculateNormals()

            for n in range(0, mb.getVertexCount()):
                v = mb.getVertex(n)
                mb.setVertexUVCoordinates(n, v[0], v[2] * aspect)
            return mb.build().getTransformed(scale_matrix)

    def _buildMesh(self, min_w: float, max_w: float, min_h: float, max_h: float, min_d: float, max_d:float, z_fight_distance: float) -> MeshData:
        if self._shape != "elliptic":
            # Outline 'cube' of the build volume
            mb = MeshBuilder()
            mb.addLine(Vector(min_w, min_h, min_d), Vector(max_w, min_h, min_d), color = self._volume_outline_color)
            mb.addLine(Vector(min_w, min_h, min_d), Vector(min_w, max_h, min_d), color = self._volume_outline_color)
            mb.addLine(Vector(min_w, max_h, min_d), Vector(max_w, max_h, min_d), color = self._volume_outline_color)
            mb.addLine(Vector(max_w, min_h, min_d), Vector(max_w, max_h, min_d), color = self._volume_outline_color)

            mb.addLine(Vector(min_w, min_h, max_d), Vector(max_w, min_h, max_d), color = self._volume_outline_color)
            mb.addLine(Vector(min_w, min_h, max_d), Vector(min_w, max_h, max_d), color = self._volume_outline_color)
            mb.addLine(Vector(min_w, max_h, max_d), Vector(max_w, max_h, max_d), color = self._volume_outline_color)
            mb.addLine(Vector(max_w, min_h, max_d), Vector(max_w, max_h, max_d), color = self._volume_outline_color)

            mb.addLine(Vector(min_w, min_h, min_d), Vector(min_w, min_h, max_d), color = self._volume_outline_color)
            mb.addLine(Vector(max_w, min_h, min_d), Vector(max_w, min_h, max_d), color = self._volume_outline_color)
            mb.addLine(Vector(min_w, max_h, min_d), Vector(min_w, max_h, max_d), color = self._volume_outline_color)
            mb.addLine(Vector(max_w, max_h, min_d), Vector(max_w, max_h, max_d), color = self._volume_outline_color)

            return mb.build()

        else:
            # Bottom and top 'ellipse' of the build volume
            scale_matrix = Matrix()
            if self._width != 0:
                # Scale circular meshes by aspect ratio if width != height
                aspect = self._depth / self._width
                scale_matrix.compose(scale = Vector(1, 1, aspect))
            mb = MeshBuilder()
            mb.addArc(max_w, Vector.Unit_Y, center = (0, min_h - z_fight_distance, 0), color = self._volume_outline_color)
            mb.addArc(max_w, Vector.Unit_Y, center = (0, max_h, 0),  color = self._volume_outline_color)
            return mb.build().getTransformed(scale_matrix)

    def _buildOriginMesh(self, origin: Vector) -> MeshData:
        mb = MeshBuilder()
        mb.addCube(
            width=self._origin_line_length,
            height=self._origin_line_width,
            depth=self._origin_line_width,
            center=origin + Vector(self._origin_line_length / 2, 0, 0),
            color=self._x_axis_color
        )
        mb.addCube(
            width=self._origin_line_width,
            height=self._origin_line_length,
            depth=self._origin_line_width,
            center=origin + Vector(0, self._origin_line_length / 2, 0),
            color=self._y_axis_color
        )
        mb.addCube(
            width=self._origin_line_width,
            height=self._origin_line_width,
            depth=self._origin_line_length,
            center=origin - Vector(0, 0, self._origin_line_length / 2),
            color=self._z_axis_color
        )
        return mb.build()

    def _updateColors(self):
        theme = self._application.getTheme()
        if theme is None:
            return
        self._volume_outline_color = Color(*theme.getColor("volume_outline").getRgb())
        self._x_axis_color = Color(*theme.getColor("x_axis").getRgb())
        self._y_axis_color = Color(*theme.getColor("y_axis").getRgb())
        self._z_axis_color = Color(*theme.getColor("z_axis").getRgb())
        self._disallowed_area_color = Color(*theme.getColor("disallowed_area").getRgb())
        self._error_area_color = Color(*theme.getColor("error_area").getRgb())

    def _buildErrorMesh(self, min_w: float, max_w: float, min_h: float, max_h: float, min_d: float, max_d: float, disallowed_area_height: float) -> Optional[MeshData]:
        if not self._error_areas:
            return None
        mb = MeshBuilder()
        for error_area in self._error_areas:
            color = self._error_area_color
            points = error_area.getPoints()
            first = Vector(self._clamp(points[0][0], min_w, max_w), disallowed_area_height,
                           self._clamp(points[0][1], min_d, max_d))
            previous_point = Vector(self._clamp(points[0][0], min_w, max_w), disallowed_area_height,
                                    self._clamp(points[0][1], min_d, max_d))
            for point in points:
                new_point = Vector(self._clamp(point[0], min_w, max_w), disallowed_area_height,
                                   self._clamp(point[1], min_d, max_d))
                mb.addFace(first, previous_point, new_point, color=color)
                previous_point = new_point
        return mb.build()

    def _buildDisallowedAreaMesh(self, min_w: float, max_w: float, min_h: float, max_h: float, min_d: float, max_d: float, disallowed_area_height: float) -> Optional[MeshData]:
        if not self._disallowed_areas:
            return None

        mb = MeshBuilder()
        color = self._disallowed_area_color
        for polygon in self._disallowed_areas:
            points = polygon.getPoints()
            if len(points) == 0:
                continue

            first = Vector(self._clamp(points[0][0], min_w, max_w), disallowed_area_height,
                           self._clamp(points[0][1], min_d, max_d))
            previous_point = Vector(self._clamp(points[0][0], min_w, max_w), disallowed_area_height,
                                    self._clamp(points[0][1], min_d, max_d))
            for point in points:
                new_point = Vector(self._clamp(point[0], min_w, max_w), disallowed_area_height,
                                   self._clamp(point[1], min_d, max_d))
                mb.addFace(first, previous_point, new_point, color=color)
                previous_point = new_point

            # Find the largest disallowed area to exclude it from the maximum scale bounds.
            # This is a very nasty hack. This pretty much only works for UM machines.
            # This disallowed area_size needs a -lot- of rework at some point in the future: TODO
            if numpy.min(points[:,
                         1]) >= 0:  # This filters out all areas that have points to the left of the centre. This is done to filter the skirt area.
                size = abs(numpy.max(points[:, 1]) - numpy.min(points[:, 1]))
            else:
                size = 0
            self._disallowed_area_size = max(size, self._disallowed_area_size)
        return mb.build()

    ##  Recalculates the build volume & disallowed areas.
    def rebuild(self) -> None:
        if not self._width or not self._height or not self._depth:
            return

        if not self._engine_ready:
            return

        if not self._global_container_stack:
            return

        if not self._volume_outline_color:
            self._updateColors()

        min_w = -self._width / 2
        max_w = self._width / 2
        min_h = 0.0
        max_h = self._height
        min_d = -self._depth / 2
        max_d = self._depth / 2

        z_fight_distance = 0.2  # Distance between buildplate and disallowed area meshes to prevent z-fighting

        self._grid_mesh = self._buildGridMesh(min_w, max_w, min_h, max_h, min_d, max_d, z_fight_distance)
        self.setMeshData(self._buildMesh(min_w, max_w, min_h, max_h, min_d, max_d, z_fight_distance))

        # Indication of the machine origin
        if self._global_container_stack.getProperty("machine_center_is_zero", "value"):
            origin = (Vector(min_w, min_h, min_d) + Vector(max_w, min_h, max_d)) / 2
        else:
            origin = Vector(min_w, min_h, max_d)

        self._origin_mesh = self._buildOriginMesh(origin)

        disallowed_area_height = 0.1
        self._disallowed_area_size = 0.
        self._disallowed_area_mesh = self._buildDisallowedAreaMesh(min_w, max_w, min_h, max_h, min_d, max_d, disallowed_area_height)

        self._error_mesh = self._buildErrorMesh(min_w, max_w, min_h, max_h, min_d, max_d, disallowed_area_height)

        self._volume_aabb = AxisAlignedBox(
            minimum = Vector(min_w, min_h - 1.0, min_d),
            maximum = Vector(max_w, max_h - self._raft_thickness - self._extra_z_clearance, max_d))

        bed_adhesion_size = self.getEdgeDisallowedSize()

        # As this works better for UM machines, we only add the disallowed_area_size for the z direction.
        # This is probably wrong in all other cases. TODO!
        # The +1 and -1 is added as there is always a bit of extra room required to work properly.
        scale_to_max_bounds = AxisAlignedBox(
            minimum = Vector(min_w + bed_adhesion_size + 1, min_h, min_d + self._disallowed_area_size - bed_adhesion_size + 1),
            maximum = Vector(max_w - bed_adhesion_size - 1, max_h - self._raft_thickness - self._extra_z_clearance, max_d - self._disallowed_area_size + bed_adhesion_size - 1)
        )

        self._application.getController().getScene()._maximum_bounds = scale_to_max_bounds  # type: ignore

        self.updateNodeBoundaryCheck()

    def getBoundingBox(self):
        return self._volume_aabb

    def getRaftThickness(self) -> float:
        return self._raft_thickness

    def _updateRaftThickness(self) -> None:
        if not self._global_container_stack:
            return

        old_raft_thickness = self._raft_thickness
        if self._global_container_stack.extruderList:
            # This might be called before the extruder stacks have initialised, in which case getting the adhesion_type fails
            self._adhesion_type = self._global_container_stack.getProperty("adhesion_type", "value")
        self._raft_thickness = 0.0
        if self._adhesion_type == "raft":
            self._raft_thickness = (
                self._global_container_stack.getProperty("raft_base_thickness", "value") +
                self._global_container_stack.getProperty("raft_interface_thickness", "value") +
                self._global_container_stack.getProperty("raft_surface_layers", "value") *
                self._global_container_stack.getProperty("raft_surface_thickness", "value") +
                self._global_container_stack.getProperty("raft_airgap", "value") -
                self._global_container_stack.getProperty("layer_0_z_overlap", "value"))

        # Rounding errors do not matter, we check if raft_thickness has changed at all
        if old_raft_thickness != self._raft_thickness:
            self.setPosition(Vector(0, -self._raft_thickness, 0), SceneNode.TransformSpace.World)
            self.raftThicknessChanged.emit()

    def _calculateExtraZClearance(self, extruders: List["ContainerStack"]) -> float:
        if not self._global_container_stack:
            return 0
        
        extra_z = 0.0
        for extruder in extruders:
            if extruder.getProperty("retraction_hop_enabled", "value"):
                retraction_hop = extruder.getProperty("retraction_hop", "value")
                if extra_z is None or retraction_hop > extra_z:
                    extra_z = retraction_hop
        return extra_z

    def _onStackChanged(self):
        self._stack_change_timer.start()

    ##  Update the build volume visualization
    def _onStackChangeTimerFinished(self) -> None:
        if self._global_container_stack:
            self._global_container_stack.propertyChanged.disconnect(self._onSettingPropertyChanged)
            extruders = ExtruderManager.getInstance().getActiveExtruderStacks()
            for extruder in extruders:
                extruder.propertyChanged.disconnect(self._onSettingPropertyChanged)

        self._global_container_stack = self._application.getGlobalContainerStack()

        if self._global_container_stack:
            self._global_container_stack.propertyChanged.connect(self._onSettingPropertyChanged)
            extruders = ExtruderManager.getInstance().getActiveExtruderStacks()
            for extruder in extruders:
                extruder.propertyChanged.connect(self._onSettingPropertyChanged)

            self._width = self._global_container_stack.getProperty("machine_width", "value")
            machine_height = self._global_container_stack.getProperty("machine_height", "value")
            if self._global_container_stack.getProperty("print_sequence", "value") == "one_at_a_time" and len(self._scene_objects) > 1:
                self._height = min(self._global_container_stack.getProperty("gantry_height", "value"), machine_height)
                if self._height < machine_height:
                    self._build_volume_message.show()
                else:
                    self._build_volume_message.hide()
            else:
                self._height = self._global_container_stack.getProperty("machine_height", "value")
                self._build_volume_message.hide()
            self._depth = self._global_container_stack.getProperty("machine_depth", "value")
            self._shape = self._global_container_stack.getProperty("machine_shape", "value")

            self._updateDisallowedAreas()
            self._updateRaftThickness()
            self._extra_z_clearance = self._calculateExtraZClearance(ExtruderManager.getInstance().getUsedExtruderStacks())

            if self._engine_ready:
                self.rebuild()

            camera = Application.getInstance().getController().getCameraTool()
            if camera:
                diagonal = self.getDiagonalSize()
                if diagonal > 1:
                    # You can zoom out up to 5 times the diagonal. This gives some space around the volume.
                    camera.setZoomRange(min = 0.1, max = diagonal * 5)  # type: ignore

    def _onEngineCreated(self) -> None:
        self._engine_ready = True
        self.rebuild()

    def _onSettingChangeTimerFinished(self) -> None:
        if not self._global_container_stack:
            return

        rebuild_me = False
        update_disallowed_areas = False
        update_raft_thickness = False
        update_extra_z_clearance = True

        for setting_key in self._changed_settings_since_last_rebuild:
            if setting_key == "print_sequence":
                machine_height = self._global_container_stack.getProperty("machine_height", "value")
                if self._application.getGlobalContainerStack().getProperty("print_sequence", "value") == "one_at_a_time" and len(self._scene_objects) > 1:
                    self._height = min(self._global_container_stack.getProperty("gantry_height", "value"), machine_height)
                    if self._height < machine_height:
                        self._build_volume_message.show()
                    else:
                        self._build_volume_message.hide()
                else:
                    self._height = self._global_container_stack.getProperty("machine_height", "value")
                    self._build_volume_message.hide()
                update_disallowed_areas = True

            # sometimes the machine size or shape settings are adjusted on the active machine, we should reflect this
            if setting_key in self._machine_settings:
                self._updateMachineSizeProperties()
                update_extra_z_clearance = True
                update_disallowed_areas = True

            if setting_key in self._disallowed_area_settings:
                update_disallowed_areas = True

            if setting_key in self._raft_settings:
                update_raft_thickness = True

            if setting_key in self._extra_z_settings:
                update_extra_z_clearance = True

            if setting_key in self._limit_to_extruder_settings:
                update_disallowed_areas = True

            rebuild_me = update_extra_z_clearance or update_disallowed_areas or update_raft_thickness

        # We only want to update all of them once.
        if update_disallowed_areas:
            self._updateDisallowedAreas()

        if update_raft_thickness:
            self._updateRaftThickness()

        if update_extra_z_clearance:
            self._extra_z_clearance = self._calculateExtraZClearance(ExtruderManager.getInstance().getUsedExtruderStacks())

        if rebuild_me:
            self.rebuild()

        # We just did a rebuild, reset the list.
        self._changed_settings_since_last_rebuild = []

    def _onSettingPropertyChanged(self, setting_key: str, property_name: str) -> None:
        if property_name != "value":
            return

        if setting_key not in self._changed_settings_since_last_rebuild:
            self._changed_settings_since_last_rebuild.append(setting_key)
            self._setting_change_timer.start()

    def hasErrors(self) -> bool:
        return self._has_errors

    def _updateMachineSizeProperties(self) -> None:
        if not self._global_container_stack:
            return
        self._height = self._global_container_stack.getProperty("machine_height", "value")
        self._width = self._global_container_stack.getProperty("machine_width", "value")
        self._depth = self._global_container_stack.getProperty("machine_depth", "value")
        self._shape = self._global_container_stack.getProperty("machine_shape", "value")

    ##  Calls _updateDisallowedAreas and makes sure the changes appear in the
    #   scene.
    #
    #   This is required for a signal to trigger the update in one go. The
    #   ``_updateDisallowedAreas`` method itself shouldn't call ``rebuild``,
    #   since there may be other changes before it needs to be rebuilt, which
    #   would hit performance.

    def _updateDisallowedAreasAndRebuild(self):
        self._updateDisallowedAreas()
        self._updateRaftThickness()
        self._extra_z_clearance = self._calculateExtraZClearance(ExtruderManager.getInstance().getUsedExtruderStacks())
        self.rebuild()

    def _updateDisallowedAreas(self) -> None:
        if not self._global_container_stack:
            return

        self._error_areas = []

        used_extruders = ExtruderManager.getInstance().getUsedExtruderStacks()
        disallowed_border_size = self.getEdgeDisallowedSize()

        result_areas = self._computeDisallowedAreasStatic(disallowed_border_size, used_extruders)  # Normal machine disallowed areas can always be added.
        prime_areas = self._computeDisallowedAreasPrimeBlob(disallowed_border_size, used_extruders)
        result_areas_no_brim = self._computeDisallowedAreasStatic(0, used_extruders)  # Where the priming is not allowed to happen. This is not added to the result, just for collision checking.

        # Check if prime positions intersect with disallowed areas.
        for extruder in used_extruders:
            extruder_id = extruder.getId()

            result_areas[extruder_id].extend(prime_areas[extruder_id])
            result_areas_no_brim[extruder_id].extend(prime_areas[extruder_id])

            nozzle_disallowed_areas = extruder.getProperty("nozzle_disallowed_areas", "value")
            for area in nozzle_disallowed_areas:
                polygon = Polygon(numpy.array(area, numpy.float32))
                polygon_disallowed_border = polygon.getMinkowskiHull(Polygon.approximatedCircle(disallowed_border_size))
                result_areas[extruder_id].append(polygon_disallowed_border)  # Don't perform the offset on these.
                result_areas_no_brim[extruder_id].append(polygon)  # No brim

        # Add prime tower location as disallowed area.
        if len([x for x in used_extruders if x.isEnabled]) > 1:  # No prime tower if only one extruder is enabled
            prime_tower_collision = False
            prime_tower_areas = self._computeDisallowedAreasPrinted(used_extruders)
            for extruder_id in prime_tower_areas:
                for area_index, prime_tower_area in enumerate(prime_tower_areas[extruder_id]):
                    for area in result_areas[extruder_id]:
                        if prime_tower_area.intersectsPolygon(area) is not None:
                            prime_tower_collision = True
                            break
                    if prime_tower_collision:  # Already found a collision.
                        break
                    if self._global_container_stack.getProperty("prime_tower_brim_enable", "value") and self._global_container_stack.getProperty("adhesion_type", "value") != "raft":
                        prime_tower_areas[extruder_id][area_index] = prime_tower_area.getMinkowskiHull(Polygon.approximatedCircle(disallowed_border_size))
                if not prime_tower_collision:
                    result_areas[extruder_id].extend(prime_tower_areas[extruder_id])
                    result_areas_no_brim[extruder_id].extend(prime_tower_areas[extruder_id])
                else:
                    self._error_areas.extend(prime_tower_areas[extruder_id])

        self._has_errors = len(self._error_areas) > 0

        self._disallowed_areas = []
        for extruder_id in result_areas:
            self._disallowed_areas.extend(result_areas[extruder_id])
        self._disallowed_areas_no_brim = []
        for extruder_id in result_areas_no_brim:
            self._disallowed_areas_no_brim.extend(result_areas_no_brim[extruder_id])

    ##  Computes the disallowed areas for objects that are printed with print
    #   features.
    #
    #   This means that the brim, travel avoidance and such will be applied to
    #   these features.
    #
    #   \return A dictionary with for each used extruder ID the disallowed areas
    #   where that extruder may not print.
    def _computeDisallowedAreasPrinted(self, used_extruders):
        result = {}
        adhesion_extruder = None #type: ExtruderStack
        for extruder in used_extruders:
            if int(extruder.getProperty("extruder_nr", "value")) == int(self._global_container_stack.getProperty("adhesion_extruder_nr", "value")):
                adhesion_extruder = extruder
            result[extruder.getId()] = []

        # Currently, the only normally printed object is the prime tower.
        if self._global_container_stack.getProperty("prime_tower_enable", "value"):
            prime_tower_size = self._global_container_stack.getProperty("prime_tower_size", "value")
            machine_width = self._global_container_stack.getProperty("machine_width", "value")
            machine_depth = self._global_container_stack.getProperty("machine_depth", "value")
            prime_tower_x = self._global_container_stack.getProperty("prime_tower_position_x", "value")
            prime_tower_y = - self._global_container_stack.getProperty("prime_tower_position_y", "value")
            if not self._global_container_stack.getProperty("machine_center_is_zero", "value"):
                prime_tower_x = prime_tower_x - machine_width / 2 #Offset by half machine_width and _depth to put the origin in the front-left.
                prime_tower_y = prime_tower_y + machine_depth / 2

            if adhesion_extruder is not None and self._global_container_stack.getProperty("prime_tower_brim_enable", "value") and self._global_container_stack.getProperty("adhesion_type", "value") != "raft":
                brim_size = (
                    adhesion_extruder.getProperty("brim_line_count", "value") *
                    adhesion_extruder.getProperty("skirt_brim_line_width", "value") / 100.0 *
                    adhesion_extruder.getProperty("initial_layer_line_width_factor", "value")
                )
                prime_tower_x -= brim_size
                prime_tower_y += brim_size

            radius = prime_tower_size / 2
            prime_tower_area = Polygon.approximatedCircle(radius)
            prime_tower_area = prime_tower_area.translate(prime_tower_x - radius, prime_tower_y - radius)

            prime_tower_area = prime_tower_area.getMinkowskiHull(Polygon.approximatedCircle(0))
            for extruder in used_extruders:
                result[extruder.getId()].append(prime_tower_area) #The prime tower location is the same for each extruder, regardless of offset.

        return result

    ##  Computes the disallowed areas for the prime blobs.
    #
    #   These are special because they are not subject to things like brim or
    #   travel avoidance. They do get a dilute with the border size though
    #   because they may not intersect with brims and such of other objects.
    #
    #   \param border_size The size with which to offset the disallowed areas
    #   due to skirt, brim, travel avoid distance, etc.
    #   \param used_extruders The extruder stacks to generate disallowed areas
    #   for.
    #   \return A dictionary with for each used extruder ID the prime areas.
    def _computeDisallowedAreasPrimeBlob(self, border_size: float, used_extruders: List["ExtruderStack"]) -> Dict[str, List[Polygon]]:
        result = {}  # type: Dict[str, List[Polygon]]
        if not self._global_container_stack:
            return result
        machine_width = self._global_container_stack.getProperty("machine_width", "value")
        machine_depth = self._global_container_stack.getProperty("machine_depth", "value")
        for extruder in used_extruders:
            prime_blob_enabled = extruder.getProperty("prime_blob_enable", "value")
            prime_x = extruder.getProperty("extruder_prime_pos_x", "value")
            prime_y = -extruder.getProperty("extruder_prime_pos_y", "value")

            # Ignore extruder prime position if it is not set or if blob is disabled
            if (prime_x == 0 and prime_y == 0) or not prime_blob_enabled:
                result[extruder.getId()] = []
                continue

            if not self._global_container_stack.getProperty("machine_center_is_zero", "value"):
                prime_x = prime_x - machine_width / 2  # Offset by half machine_width and _depth to put the origin in the front-left.
                prime_y = prime_y + machine_depth / 2

            prime_polygon = Polygon.approximatedCircle(PRIME_CLEARANCE)
            prime_polygon = prime_polygon.getMinkowskiHull(Polygon.approximatedCircle(border_size))

            prime_polygon = prime_polygon.translate(prime_x, prime_y)
            result[extruder.getId()] = [prime_polygon]

        return result

    ##  Computes the disallowed areas that are statically placed in the machine.
    #
    #   It computes different disallowed areas depending on the offset of the
    #   extruder. The resulting dictionary will therefore have an entry for each
    #   extruder that is used.
    #
    #   \param border_size The size with which to offset the disallowed areas
    #   due to skirt, brim, travel avoid distance, etc.
    #   \param used_extruders The extruder stacks to generate disallowed areas
    #   for.
    #   \return A dictionary with for each used extruder ID the disallowed areas
    #   where that extruder may not print.
    def _computeDisallowedAreasStatic(self, border_size:float, used_extruders: List["ExtruderStack"]) -> Dict[str, List[Polygon]]:
        # Convert disallowed areas to polygons and dilate them.
        machine_disallowed_polygons = []
        if self._global_container_stack is None:
            return {}

        for area in self._global_container_stack.getProperty("machine_disallowed_areas", "value"):
            polygon = Polygon(numpy.array(area, numpy.float32))
            polygon = polygon.getMinkowskiHull(Polygon.approximatedCircle(border_size))
            machine_disallowed_polygons.append(polygon)

        # For certain machines we don't need to compute disallowed areas for each nozzle.
        # So we check here and only do the nozzle offsetting if needed.
        nozzle_offsetting_for_disallowed_areas = self._global_container_stack.getMetaDataEntry(
            "nozzle_offsetting_for_disallowed_areas", True)

        result = {}  # type: Dict[str, List[Polygon]]
        for extruder in used_extruders:
            extruder_id = extruder.getId()
            offset_x = extruder.getProperty("machine_nozzle_offset_x", "value")
            if offset_x is None:
                offset_x = 0
            offset_y = extruder.getProperty("machine_nozzle_offset_y", "value")
            if offset_y is None:
                offset_y = 0
            offset_y = -offset_y  # Y direction of g-code is the inverse of Y direction of Cura's scene space.
            result[extruder_id] = []

            for polygon in machine_disallowed_polygons:
                result[extruder_id].append(polygon.translate(offset_x, offset_y))  # Compensate for the nozzle offset of this extruder.

            # Add the border around the edge of the build volume.
            left_unreachable_border = 0
            right_unreachable_border = 0
            top_unreachable_border = 0
            bottom_unreachable_border = 0

            # Only do nozzle offsetting if needed
            if nozzle_offsetting_for_disallowed_areas:
                # The build volume is defined as the union of the area that all extruders can reach, so we need to know
                # the relative offset to all extruders.
                for other_extruder in ExtruderManager.getInstance().getActiveExtruderStacks():
                    other_offset_x = other_extruder.getProperty("machine_nozzle_offset_x", "value")
                    if other_offset_x is None:
                        other_offset_x = 0
                    other_offset_y = other_extruder.getProperty("machine_nozzle_offset_y", "value")
                    if other_offset_y is None:
                        other_offset_y = 0
                    other_offset_y = -other_offset_y
                    left_unreachable_border = min(left_unreachable_border, other_offset_x - offset_x)
                    right_unreachable_border = max(right_unreachable_border, other_offset_x - offset_x)
                    top_unreachable_border = min(top_unreachable_border, other_offset_y - offset_y)
                    bottom_unreachable_border = max(bottom_unreachable_border, other_offset_y - offset_y)
            half_machine_width = self._global_container_stack.getProperty("machine_width", "value") / 2
            half_machine_depth = self._global_container_stack.getProperty("machine_depth", "value") / 2

            if self._shape != "elliptic":
                if border_size - left_unreachable_border > 0:
                    result[extruder_id].append(Polygon(numpy.array([
                        [-half_machine_width, -half_machine_depth],
                        [-half_machine_width, half_machine_depth],
                        [-half_machine_width + border_size - left_unreachable_border, half_machine_depth - border_size - bottom_unreachable_border],
                        [-half_machine_width + border_size - left_unreachable_border, -half_machine_depth + border_size - top_unreachable_border]
                    ], numpy.float32)))
                if border_size + right_unreachable_border > 0:
                    result[extruder_id].append(Polygon(numpy.array([
                        [half_machine_width, half_machine_depth],
                        [half_machine_width, -half_machine_depth],
                        [half_machine_width - border_size - right_unreachable_border, -half_machine_depth + border_size - top_unreachable_border],
                        [half_machine_width - border_size - right_unreachable_border, half_machine_depth - border_size - bottom_unreachable_border]
                    ], numpy.float32)))
                if border_size + bottom_unreachable_border > 0:
                    result[extruder_id].append(Polygon(numpy.array([
                        [-half_machine_width, half_machine_depth],
                        [half_machine_width, half_machine_depth],
                        [half_machine_width - border_size - right_unreachable_border, half_machine_depth - border_size - bottom_unreachable_border],
                        [-half_machine_width + border_size - left_unreachable_border, half_machine_depth - border_size - bottom_unreachable_border]
                    ], numpy.float32)))
                if border_size - top_unreachable_border > 0:
                    result[extruder_id].append(Polygon(numpy.array([
                        [half_machine_width, -half_machine_depth],
                        [-half_machine_width, -half_machine_depth],
                        [-half_machine_width + border_size - left_unreachable_border, -half_machine_depth + border_size - top_unreachable_border],
                        [half_machine_width - border_size - right_unreachable_border, -half_machine_depth + border_size - top_unreachable_border]
                    ], numpy.float32)))
            else:
                sections = 32
                arc_vertex = [0, half_machine_depth - border_size]
                for i in range(0, sections):
                    quadrant = math.floor(4 * i / sections)
                    vertices = []
                    if quadrant == 0:
                        vertices.append([-half_machine_width, half_machine_depth])
                    elif quadrant == 1:
                        vertices.append([-half_machine_width, -half_machine_depth])
                    elif quadrant == 2:
                        vertices.append([half_machine_width, -half_machine_depth])
                    elif quadrant == 3:
                        vertices.append([half_machine_width, half_machine_depth])
                    vertices.append(arc_vertex)

                    angle = 2 * math.pi * (i + 1) / sections
                    arc_vertex = [-(half_machine_width - border_size) * math.sin(angle), (half_machine_depth - border_size) * math.cos(angle)]
                    vertices.append(arc_vertex)

                    result[extruder_id].append(Polygon(numpy.array(vertices, numpy.float32)))

                if border_size > 0:
                    result[extruder_id].append(Polygon(numpy.array([
                        [-half_machine_width, -half_machine_depth],
                        [-half_machine_width, half_machine_depth],
                        [-half_machine_width + border_size, 0]
                    ], numpy.float32)))
                    result[extruder_id].append(Polygon(numpy.array([
                        [-half_machine_width, half_machine_depth],
                        [ half_machine_width, half_machine_depth],
                        [ 0, half_machine_depth - border_size]
                    ], numpy.float32)))
                    result[extruder_id].append(Polygon(numpy.array([
                        [ half_machine_width, half_machine_depth],
                        [ half_machine_width, -half_machine_depth],
                        [ half_machine_width - border_size, 0]
                    ], numpy.float32)))
                    result[extruder_id].append(Polygon(numpy.array([
                        [ half_machine_width, -half_machine_depth],
                        [-half_machine_width, -half_machine_depth],
                        [ 0, -half_machine_depth + border_size]
                    ], numpy.float32)))

        return result

    ##  Private convenience function to get a setting from every extruder.
    #
    #   For single extrusion machines, this gets the setting from the global
    #   stack.
    #
    #   \return A sequence of setting values, one for each extruder.
    def _getSettingFromAllExtruders(self, setting_key: str) -> List[Any]:
        all_values = ExtruderManager.getInstance().getAllExtruderSettings(setting_key, "value")
        all_types = ExtruderManager.getInstance().getAllExtruderSettings(setting_key, "type")
        for i, (setting_value, setting_type) in enumerate(zip(all_values, all_types)):
            if not setting_value and (setting_type == "int" or setting_type == "float"):
                all_values[i] = 0
        return all_values

    def _calculateBedAdhesionSize(self, used_extruders):
        if self._global_container_stack is None:
            return

        container_stack = self._global_container_stack
        adhesion_type = container_stack.getProperty("adhesion_type", "value")
        skirt_brim_line_width = self._global_container_stack.getProperty("skirt_brim_line_width", "value")
        initial_layer_line_width_factor = self._global_container_stack.getProperty("initial_layer_line_width_factor", "value")
        # Use brim width if brim is enabled OR the prime tower has a brim.
        if adhesion_type == "brim" or (self._global_container_stack.getProperty("prime_tower_brim_enable", "value") and adhesion_type != "raft"):
            brim_line_count = self._global_container_stack.getProperty("brim_line_count", "value")
            bed_adhesion_size = skirt_brim_line_width * brim_line_count * initial_layer_line_width_factor / 100.0

            for extruder_stack in used_extruders:
                bed_adhesion_size += extruder_stack.getProperty("skirt_brim_line_width", "value") * extruder_stack.getProperty("initial_layer_line_width_factor", "value") / 100.0

            # We don't create an additional line for the extruder we're printing the brim with.
            bed_adhesion_size -= skirt_brim_line_width * initial_layer_line_width_factor / 100.0
        elif adhesion_type == "skirt":  # No brim? Also not on prime tower? Then use whatever the adhesion type is saying: Skirt, raft or none.
            skirt_distance = self._global_container_stack.getProperty("skirt_gap", "value")
            skirt_line_count = self._global_container_stack.getProperty("skirt_line_count", "value")

            bed_adhesion_size = skirt_distance + (
                        skirt_brim_line_width * skirt_line_count) * initial_layer_line_width_factor / 100.0

            for extruder_stack in used_extruders:
                bed_adhesion_size += extruder_stack.getProperty("skirt_brim_line_width", "value") * extruder_stack.getProperty("initial_layer_line_width_factor", "value") / 100.0

            # We don't create an additional line for the extruder we're printing the skirt with.
            bed_adhesion_size -= skirt_brim_line_width * initial_layer_line_width_factor / 100.0
        elif adhesion_type == "raft":
            bed_adhesion_size = self._global_container_stack.getProperty("raft_margin", "value")
        elif adhesion_type == "none":
            bed_adhesion_size = 0
        else:
            raise Exception("Unknown bed adhesion type. Did you forget to update the build volume calculations for your new bed adhesion type?")

        max_length_available = 0.5 * min(
            self._global_container_stack.getProperty("machine_width", "value"),
            self._global_container_stack.getProperty("machine_depth", "value")
        )
        bed_adhesion_size = min(bed_adhesion_size, max_length_available)
        return bed_adhesion_size

    def _calculateFarthestShieldDistance(self, container_stack):
        farthest_shield_distance = 0
        if container_stack.getProperty("draft_shield_enabled", "value"):
            farthest_shield_distance = max(farthest_shield_distance, container_stack.getProperty("draft_shield_dist", "value"))
        if container_stack.getProperty("ooze_shield_enabled", "value"):
            farthest_shield_distance = max(farthest_shield_distance,container_stack.getProperty("ooze_shield_dist", "value"))
        return farthest_shield_distance

    def _calculateSupportExpansion(self, container_stack):
        support_expansion = 0
        support_enabled = self._global_container_stack.getProperty("support_enable", "value")
        support_offset = self._global_container_stack.getProperty("support_offset", "value")
        if support_enabled and support_offset:
            support_expansion += support_offset
        return support_expansion

    def _calculateMoveFromWallRadius(self, used_extruders):
        move_from_wall_radius = 0  # Moves that start from outer wall.
        all_values = [move_from_wall_radius]
        all_values.extend(self._getSettingFromAllExtruders("infill_wipe_dist"))
        move_from_wall_radius = max(all_values)
        avoid_enabled_per_extruder = [stack.getProperty("travel_avoid_other_parts", "value") for stack in used_extruders]
        travel_avoid_distance_per_extruder = [stack.getProperty("travel_avoid_distance", "value") for stack in used_extruders]
        for avoid_other_parts_enabled, avoid_distance in zip(avoid_enabled_per_extruder, travel_avoid_distance_per_extruder):  # For each extruder (or just global).
            if avoid_other_parts_enabled:
                move_from_wall_radius = max(move_from_wall_radius, avoid_distance)
        return move_from_wall_radius

    ##  Calculate the disallowed radius around the edge.
    #
    #   This disallowed radius is to allow for space around the models that is
    #   not part of the collision radius, such as bed adhesion (skirt/brim/raft)
    #   and travel avoid distance.
    def getEdgeDisallowedSize(self):
        if not self._global_container_stack or not self._global_container_stack.extruderList:
            return 0

        container_stack = self._global_container_stack
        used_extruders = ExtruderManager.getInstance().getUsedExtruderStacks()

        # If we are printing one at a time, we need to add the bed adhesion size to the disallowed areas of the objects
        if container_stack.getProperty("print_sequence", "value") == "one_at_a_time":
            return 0.1

        bed_adhesion_size = self._calculateBedAdhesionSize(used_extruders)
        support_expansion = self._calculateSupportExpansion(self._global_container_stack)
        farthest_shield_distance = self._calculateFarthestShieldDistance(self._global_container_stack)
        move_from_wall_radius = self._calculateMoveFromWallRadius(used_extruders)

        # Now combine our different pieces of data to get the final border size.
        # Support expansion is added to the bed adhesion, since the bed adhesion goes around support.
        # Support expansion is added to farthest shield distance, since the shields go around support.
        border_size = max(move_from_wall_radius, support_expansion + farthest_shield_distance, support_expansion + bed_adhesion_size)
        return border_size

    def _clamp(self, value, min_value, max_value):
        return max(min(value, max_value), min_value)

    _machine_settings = ["machine_width", "machine_depth", "machine_height", "machine_shape", "machine_center_is_zero"]
    _skirt_settings = ["adhesion_type", "skirt_gap", "skirt_line_count", "skirt_brim_line_width", "brim_width", "brim_line_count", "raft_margin", "draft_shield_enabled", "draft_shield_dist", "initial_layer_line_width_factor"]
    _raft_settings = ["adhesion_type", "raft_base_thickness", "raft_interface_thickness", "raft_surface_layers", "raft_surface_thickness", "raft_airgap", "layer_0_z_overlap"]
    _extra_z_settings = ["retraction_hop_enabled", "retraction_hop"]
    _prime_settings = ["extruder_prime_pos_x", "extruder_prime_pos_y", "extruder_prime_pos_z", "prime_blob_enable"]
    _tower_settings = ["prime_tower_enable", "prime_tower_size", "prime_tower_position_x", "prime_tower_position_y", "prime_tower_brim_enable"]
    _ooze_shield_settings = ["ooze_shield_enabled", "ooze_shield_dist"]
    _distance_settings = ["infill_wipe_dist", "travel_avoid_distance", "support_offset", "support_enable", "travel_avoid_other_parts", "travel_avoid_supports"]
    _extruder_settings = ["support_enable", "support_bottom_enable", "support_roof_enable", "support_infill_extruder_nr", "support_extruder_nr_layer_0", "support_bottom_extruder_nr", "support_roof_extruder_nr", "brim_line_count", "adhesion_extruder_nr", "adhesion_type"] #Settings that can affect which extruders are used.
    _limit_to_extruder_settings = ["wall_extruder_nr", "wall_0_extruder_nr", "wall_x_extruder_nr", "top_bottom_extruder_nr", "infill_extruder_nr", "support_infill_extruder_nr", "support_extruder_nr_layer_0", "support_bottom_extruder_nr", "support_roof_extruder_nr", "adhesion_extruder_nr"]
    _disallowed_area_settings = _skirt_settings + _prime_settings + _tower_settings + _ooze_shield_settings + _distance_settings + _extruder_settings
