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
                    
        else: 
            if not self._node.getMeshData():
                return
            mesh = self._node.getMeshData()
            vertex_data = mesh.getTransformed(self._node.getWorldTransformation()).getVertices()

            hull = Polygon(numpy.rint(vertex_data[:, [0, 2]]).astype(int))
        
        # First, calculate the normal convex hull around the points
        hull = hull.getConvexHull()
        #print("hull: " , self._node.callDecoration("isGroup"), " " , hull.getPoints())
        # Then, do a Minkowski hull with a simple 1x1 quad to outset and round the normal convex hull.
        hull = hull.getMinkowskiHull(Polygon(numpy.array([[-1, -1], [-1, 1], [1, 1], [1, -1]], numpy.float32)))
       
        hull_node = ConvexHullNode.ConvexHullNode(self._node, hull, Application.getInstance().getController().getScene().getRoot())
        self._node.callDecoration("setConvexHullNode", hull_node)
        self._node.callDecoration("setConvexHull", hull)
        self._node.callDecoration("setConvexHullJob", None)
        
        if self._node.getParent().callDecoration("isGroup"):
            self._node.getParent().callDecoration("setConvexHull", None)
         #   if self._node.getParent().callDecoration("getConvexHull"):
               
        #        self._node.getParent().callDecoration("getConvexHullNode").setParent(None)
        #        self._node.getParent().callDecoration("setConvexHull", None)
        #        self._node.getParent().callDecoration("setConvexHullJob", None)
           #if hasattr(self._node.getParent(), "_convex_hull"):
               # convex_hull =  getattr(self._node.getParent(), "_convex_hull")
                
                #delattr(self._node.getParent(), "_convex_hull")
            
