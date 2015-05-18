# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Scene.SceneNode import SceneNode
from UM.Resources import Resources
from UM.Math.Color import Color
from UM.Math.Vector import Vector
from UM.Mesh.MeshData import MeshData

import numpy

class ConvexHullNode(SceneNode):
    def __init__(self, node, hull, parent = None):
        super().__init__(parent)

        self.setCalculateBoundingBox(False)

        self._material = None

        self._original_parent = parent

        self._inherit_orientation = False
        self._inherit_scale = False

        self._node = node
        self._node.transformationChanged.connect(self._onNodePositionChanged)
        self._node.parentChanged.connect(self._onNodeParentChanged)
        #self._onNodePositionChanged(self._node)

        self._hull = hull

        hull_points = self._hull.getPoints()
        center = (hull_points.min(0) + hull_points.max(0)) / 2.0

        mesh = MeshData()
        mesh.addVertex(center[0], 0.1, center[1])

        for point in hull_points:
            mesh.addVertex(point[0], 0.1, point[1])

        indices = []
        for i in range(len(hull_points) - 1):
            indices.append([0, i + 1, i + 2])

        indices.append([0, mesh.getVertexCount() - 1, 1])

        mesh.addIndices(numpy.array(indices, numpy.int32))

        self.setMeshData(mesh)

    def render(self, renderer):
        if not self._material:
            self._material = renderer.createMaterial(Resources.getPath(Resources.ShadersLocation, "basic.vert"), Resources.getPath(Resources.ShadersLocation, "color.frag"))

            self._material.setUniformValue("u_color", Color(35, 35, 35, 128))

        renderer.queueNode(self, material = self._material, transparent = True)

        return True

    def _onNodePositionChanged(self, node):
        #self.setPosition(node.getWorldPosition())
        if hasattr(node, "_convex_hull"):
            delattr(node, "_convex_hull")
            self.setParent(None)


        #self._node.transformationChanged.disconnect(self._onNodePositionChanged)
        #self._node.parentChanged.disconnect(self._onNodeParentChanged)

    def _onNodeParentChanged(self, node):
        if node.getParent():
            self.setParent(self._original_parent)
        else:
            self.setParent(None)
