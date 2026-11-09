# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional, TYPE_CHECKING
import numpy

from UM.Application import Application
from UM.Math.Polygon import Polygon
from UM.Qt.QtApplication import QtApplication
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Resources import Resources
from UM.Math.Color import Color
from UM.Math.Vector import Vector
from UM.Math.Matrix import Matrix
from UM.Mesh.MeshBuilder import MeshBuilder  # To create a mesh to display the convex hull with.
from UM.View.GL.OpenGL import OpenGL

if TYPE_CHECKING:
    from UM.Mesh.MeshData import MeshData


class ConvexHullNode(SceneNode):
    shader = None  # To prevent the shader from being re-built over and over again, only load it once.

    def __init__(self, node: SceneNode, hull: Optional[Polygon], thickness: float, parent: Optional[SceneNode] = None) -> None:
        """Convex hull node is a special type of scene node that is used to display an area, to indicate the

        location an object uses on the buildplate. This area (or area's in case of one at a time printing) is
        then displayed as a transparent shadow. If the adhesion type is set to raft, the area is extruded
        to represent the raft as well.
        """
        super().__init__(parent)

        self.setCalculateBoundingBox(False)

        self._original_parent = parent

        # Color of the drawn convex hull
        if not Application.getInstance().getIsHeadLess():
            theme = QtApplication.getInstance().getTheme()
            if theme:
                self._color = Color(*theme.getColor("convex_hull").getRgb())
            else:
                self._color = Color(0, 0, 0)
        else:
            self._color = Color(0, 0, 0)

        # The y-coordinate of the convex hull mesh. Must not be 0, to prevent z-fighting.
        self._mesh_height = 0.1

        self._thickness = thickness

        # The node this mesh is "watching"
        self._node = node
        self._source_mesh = node.getMeshData()
        self._source_world_transform = node.getWorldTransformation()
        self._source_descendants = tuple(
            (child, child.getMeshData(), child.getParent(), child.getLocalTransformation())
            for child in DepthFirstIterator(node) if child is not node
        ) if self._source_mesh is None else ()
        # Area of the head + fans for display as a shadow on the buildplate
        self._convex_hull_head_mesh = None  # type: Optional[MeshData]

        self._node.decoratorsChanged.connect(self._onNodeDecoratorsChanged)
        self._onNodeDecoratorsChanged(self._node)

        self._hull = hull
        if self._hull:
            hull_mesh_builder = MeshBuilder()
            if self._thickness == 0:
                if hull_mesh_builder.addConvexPolygon(
                    self._hull.getPoints()[::],  # bottom layer is reversed
                    self._mesh_height, color = self._color):
                    hull_mesh_builder.resetNormals()

                    hull_mesh = hull_mesh_builder.build()
                    self.setMeshData(hull_mesh)
            else:
                if hull_mesh_builder.addConvexPolygonExtrusion(
                    self._hull.getPoints()[::-1],  # bottom layer is reversed
                    self._mesh_height - thickness, self._mesh_height, color = self._color):
                    hull_mesh_builder.resetNormals()
                    hull_mesh = hull_mesh_builder.build()
                    self.setMeshData(hull_mesh)

    def getTranslationDelta(self) -> Optional[Vector]:
        """Return planar-compatible movement since the footprint mesh was built."""
        baseline = getattr(self, "_source_world_transform", None)
        if baseline is None or self._node.getMeshData() is not self._source_mesh:
            return None
        if self._source_mesh is None:
            descendants = tuple(child for child in DepthFirstIterator(self._node) if child is not self._node)
            snapshot = self._source_descendants
            if len(descendants) != len(snapshot) or not any(mesh is not None for _, mesh, _, _ in snapshot):
                return None
            for current_node, (old_node, mesh, parent, local_transform) in zip(descendants, snapshot):
                if current_node is not old_node or current_node.getMeshData() is not mesh or current_node.getParent() is not parent:
                    return None
                if not numpy.allclose(current_node.getLocalTransformation(copy = False).getData(), local_transform.getData(), rtol = 0, atol = 1e-10):
                    return None
        current = self._node.getWorldTransformation(copy = False)
        # World-space translation may introduce roundoff through inverse matrix
        # multiplication. Do not mistake that for a rotation or scale change.
        if not numpy.allclose(current.getData()[:3, :3], baseline.getData()[:3, :3], rtol = 0, atol = 1e-10):
            return None
        return current.getTranslation() - baseline.getTranslation()

    def getWorldTransformation(self, copy = True) -> Matrix:
        transformation = super().getWorldTransformation(copy = copy)
        delta = self.getTranslationDelta()
        if delta is None or (delta.x == 0 and delta.z == 0):
            return transformation
        if not copy:
            transformation = transformation.copy()
        # Footprint geometry is already in world coordinates. Keep it on the
        # plate and apply only the planar movement since its construction.
        transformation.setTranslation(transformation.getTranslation() + Vector(delta.x, 0, delta.z))
        return transformation

    def getHull(self):
        return self._hull

    def getThickness(self):
        return self._thickness

    def getWatchedNode(self):
        return self._node

    def render(self, renderer):
        if not ConvexHullNode.shader:
            ConvexHullNode.shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "transparent_object.shader"))
            ConvexHullNode.shader.setUniformValue("u_diffuseColor", self._color)
            ConvexHullNode.shader.setUniformValue("u_opacity", 0.6)
        batch = renderer.getNamedBatch("convex_hull_node")
        if not batch:
            batch = renderer.createRenderBatch(transparent = True, shader = ConvexHullNode.shader, backface_cull = True, sort = -8)
            renderer.addRenderBatch(batch, name = "convex_hull_node")
        batch.addItem(self.getWorldTransformation(copy = False), self.getMeshData())
        if self._convex_hull_head_mesh:
            # The full head. Rendered as a hint to the user: If this area overlaps another object A; this object
            # cannot be printed after A, because the head would hit A while printing the current object
            renderer.queueNode(self, shader = ConvexHullNode.shader, transparent = True, mesh = self._convex_hull_head_mesh, backface_cull = True, sort = -8)

        return True

    def _onNodeDecoratorsChanged(self, node: SceneNode) -> None:
        convex_hull_head = self._node.callDecoration("getConvexHullHeadFull")
        if convex_hull_head:
            convex_hull_head_builder = MeshBuilder()
            convex_hull_head_builder.addConvexPolygon(convex_hull_head.getPoints(), self._mesh_height - self._thickness)
            self._convex_hull_head_mesh = convex_hull_head_builder.build()
