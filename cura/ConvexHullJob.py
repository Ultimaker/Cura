# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Job import Job
from UM.Application import Application
from UM.Math.Polygon import Polygon

import numpy
import copy
from . import ConvexHullNode

class ConvexHullJob(Job):
    def __init__(self, node):
        super().__init__()

        self._node = node

    def run(self):
        if not self._node:
            return
        ## If the scene node is a group, use the hull of the children to calculate its hull.
        if self._node.callDecoration("isGroup"):
            hull = Polygon(numpy.zeros((0, 2), dtype=numpy.int32))
            for child in self._node.getChildren():
                child_hull = child.callDecoration("getConvexHull") 
                if child_hull:
                    hull.setPoints(numpy.append(hull.getPoints(), child_hull.getPoints(), axis = 0))

                if hull.getPoints().size < 3:
                    self._node.callDecoration("setConvexHull", None)
                    self._node.callDecoration("setConvexHullJob", None)
                    return

                Job.yieldThread()

        else: 
            if not self._node.getMeshData():
                return
            mesh = self._node.getMeshData()
            vertex_data = mesh.getTransformed(self._node.getWorldTransformation()).getVertices()
            # Don't use data below 0. TODO; We need a better check for this as this gives poor results for meshes with long edges.
            vertex_data = vertex_data[vertex_data[:,1] >= 0]
            hull = Polygon(numpy.rint(vertex_data[:, [0, 2]]).astype(int))

        # First, calculate the normal convex hull around the points
        hull = hull.getConvexHull()

        # Then, do a Minkowski hull with a simple 1x1 quad to outset and round the normal convex hull.
        # This is done because of rounding errors.
        hull = hull.getMinkowskiHull(Polygon(numpy.array([[-1, -1], [-1, 1], [1, 1], [1, -1]], numpy.float32)))

        profile = Application.getInstance().getMachineManager().getWorkingProfile()
        if profile:
            if profile.getSettingValue("print_sequence") == "one_at_a_time" and not self._node.getParent().callDecoration("isGroup"):
                # Printing one at a time and it's not an object in a group
                self._node.callDecoration("setConvexHullBoundary", copy.deepcopy(hull))
                head_and_fans = Polygon(numpy.array(profile.getSettingValue("machine_head_with_fans_polygon"), numpy.float32))
                # Full head hull is used to actually check the order.
                full_head_hull = hull.getMinkowskiHull(head_and_fans)
                self._node.callDecoration("setConvexHullHeadFull", full_head_hull)
                mirrored = copy.deepcopy(head_and_fans)
                mirrored.mirror([0, 0], [0, 1]) #Mirror horizontally.
                mirrored.mirror([0, 0], [1, 0]) #Mirror vertically.
                head_and_fans = head_and_fans.intersectionConvexHulls(mirrored)
                # Min head hull is used for the push free
                min_head_hull = hull.getMinkowskiHull(head_and_fans)
                self._node.callDecoration("setConvexHullHead", min_head_hull)
                hull = hull.getMinkowskiHull(Polygon(numpy.array(profile.getSettingValue("machine_head_polygon"),numpy.float32)))
            else:
                self._node.callDecoration("setConvexHullHead", None)
        if self._node.getParent() is None: #Node was already deleted before job is done.
            self._node.callDecoration("setConvexHullNode",None)
            self._node.callDecoration("setConvexHull", None)
            self._node.callDecoration("setConvexHullJob", None)
            return
        hull_node = ConvexHullNode.ConvexHullNode(self._node, hull, Application.getInstance().getController().getScene().getRoot())
        self._node.callDecoration("setConvexHullNode", hull_node)
        self._node.callDecoration("setConvexHull", hull)
        self._node.callDecoration("setConvexHullJob", None)

        if self._node.getParent() and self._node.getParent().callDecoration("isGroup"):
            job = self._node.getParent().callDecoration("getConvexHullJob")
            if job:
                job.cancel()
            self._node.getParent().callDecoration("setConvexHull", None)
            hull_node = self._node.getParent().callDecoration("getConvexHullNode")
            if hull_node:
                hull_node.setParent(None)
