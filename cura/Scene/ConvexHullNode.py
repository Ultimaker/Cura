# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional

from UM.Application import Application
from UM.Math.Polygon import Polygon
from UM.Qt.QtApplication import QtApplication
from UM.Scene.SceneNode import SceneNode
from UM.Resources import Resources
from UM.Math.Color import Color
from UM.Mesh.MeshBuilder import MeshBuilder  # To create a mesh to display the convex hull with.
from UM.View.GL.OpenGL import OpenGL


class ConvexHullNode(SceneNode):
    shader = None  # To prevent the shader from being re-built over and over again, only load it once.

    ##  Convex hull node is a special type of scene node that is used to display an area, to indicate the
    #   location an object uses on the buildplate. This area (or area's in case of one at a time printing) is
    #   then displayed as a transparent shadow. If the adhesion type is set to raft, the area is extruded
    #   to represent the raft as well.
    def __init__(self, node: SceneNode, hull: Optional[Polygon], thickness: float, parent: Optional[SceneNode] = None) -> None:
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
        # Area of the head + fans for display as a shadow on the buildplate
        self._convex_hull_head_mesh = None

        self._node.decoratorsChanged.connect(self._onNodeDecoratorsChanged)
        self._onNodeDecoratorsChanged(self._node)

        self._hull = hull
        if self._hull:
            hull_mesh_builder = MeshBuilder()

            if hull_mesh_builder.addConvexPolygonExtrusion(
                self._hull.getPoints()[::-1],  # bottom layer is reversed
                self._mesh_height - thickness, self._mesh_height, color = self._color):

                hull_mesh = hull_mesh_builder.build()
                self.setMeshData(hull_mesh)

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

        if self.getParent():
            if self.getMeshData() and isinstance(self._node, SceneNode) and self._node.callDecoration("getBuildPlateNumber") == Application.getInstance().getMultiBuildPlateModel().activeBuildPlate:
                # The object itself (+ adhesion in one-at-a-time mode)
                renderer.queueNode(self, transparent = True, shader = ConvexHullNode.shader, backface_cull = True, sort = -8)
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

        if not node:
            return

