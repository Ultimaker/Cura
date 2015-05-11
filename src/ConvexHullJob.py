# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Job import Job
from UM.Application import Application
from UM.Math.Polygon import Polygon

import numpy

from . import ConvexHullNode

class ConvexHullJob(Job):
    def __init__(self, node):
        super().__init__()

        self._node = node

    def run(self):
        if not self._node or not self._node.getMeshData():
            return

        mesh = self._node.getMeshData()
        vertexData = mesh.getTransformed(self._node.getWorldTransformation()).getVertices()

        hull = Polygon(numpy.rint(vertexData[:, [0, 2]]).astype(int))

        # First, calculate the normal convex hull around the points
        hull = hull.getConvexHull()
        # Then, do a Minkowski hull with a simple 1x1 quad to outset and round the normal convex hull.
        hull = hull.getMinkowskiHull(Polygon(numpy.array([[-1, -1], [-1, 1], [1, 1], [1, -1]], numpy.float32)))

        hull_node = ConvexHullNode.ConvexHullNode(self._node, hull, Application.getInstance().getController().getScene().getRoot())

        self._node._convex_hull = hull
        delattr(self._node, "_convex_hull_job")
