# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Scene.SceneNode import SceneNode
from UM.Resources import Resources
from UM.Math.Color import Color
from UM.Math.Vector import Vector
from UM.Mesh.MeshData import MeshData

from UM.View.GL.OpenGL import OpenGL

import numpy

class ConvexHullNode(SceneNode):
    def __init__(self, node, hull, parent = None):
        super().__init__(parent)

        self.setCalculateBoundingBox(False)

        self._shader = None

        self._original_parent = parent

        self._inherit_orientation = False
        self._inherit_scale = False

        self._color = Color(35, 35, 35, 128)

        self._node = node
        self._node.transformationChanged.connect(self._onNodePositionChanged)
        self._node.parentChanged.connect(self._onNodeParentChanged)
        self._node.decoratorsChanged.connect(self._onNodeDecoratorsChanged)
        self._onNodeDecoratorsChanged(self._node)
        self.convexHullHeadMesh = None
        self._hull = hull

        hull_points = self._hull.getPoints()
        hull_mesh = self.createHullMesh(self._hull.getPoints())
        if hull_mesh:
            self.setMeshData(hull_mesh)
        convex_hull_head = self._node.callDecoration("getConvexHullHead")
        if convex_hull_head:
            self.convexHullHeadMesh = self.createHullMesh(convex_hull_head.getPoints())

    def createHullMesh(self, hull_points):
        mesh = MeshData()
        if len(hull_points) > 3:
            center = (hull_points.min(0) + hull_points.max(0)) / 2.0
            mesh.addVertex(center[0], 0.1, center[1])
        else:
            return None
        for point in hull_points:
            mesh.addVertex(point[0], 0.1, point[1])
        indices = []
        for i in range(len(hull_points) - 1):
            indices.append([0, i + 1, i + 2])

        indices.append([0, mesh.getVertexCount() - 1, 1])

        mesh.addIndices(numpy.array(indices, numpy.int32))
        return mesh

    def getWatchedNode(self):
        return self._node

    def render(self, renderer):
        if not self._shader:
            self._shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "default.shader"))
            self._shader.setUniformValue("u_color", self._color)

        if self.getParent():
            renderer.queueNode(self, transparent = True, shader = self._shader)
            if self.convexHullHeadMesh:
                renderer.queueNode(self, shader = self._shader, transparent = True, mesh = self.convexHullHeadMesh)

        return True

    def _onNodePositionChanged(self, node):
        if node.callDecoration("getConvexHull"): 
            node.callDecoration("setConvexHull", None)
            node.callDecoration("setConvexHullNode", None)
            self.setParent(None)

    def _onNodeParentChanged(self, node):
        if node.getParent():
            self.setParent(self._original_parent)
        else:
            self.setParent(None)

    def _onNodeDecoratorsChanged(self, node):
        self._color = Color(35, 35, 35, 0.5)

        if not node:
            return

        if node.hasDecoration("getProfile"):
            self._color.setR(0.75)

        if node.hasDecoration("getSetting"):
            self._color.setG(0.75)
