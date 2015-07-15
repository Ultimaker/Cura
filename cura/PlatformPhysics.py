# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import QTimer

from UM.Scene.SceneNode import SceneNode
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator
from UM.Operations.TranslateOperation import TranslateOperation
from UM.Operations.ScaleToBoundsOperation import ScaleToBoundsOperation
from UM.Math.Float import Float
from UM.Math.Vector import Vector
from UM.Math.AxisAlignedBox import AxisAlignedBox
from UM.Application import Application
from UM.Scene.Selection import Selection
from cura.ConvexHullDecorator import ConvexHullDecorator

from . import PlatformPhysicsOperation
from . import ConvexHullJob

import time
import threading

class PlatformPhysics:
    def __init__(self, controller, volume):
        super().__init__()
        self._controller = controller
        self._controller.getScene().sceneChanged.connect(self._onSceneChanged)
        self._controller.toolOperationStarted.connect(self._onToolOperationStarted)
        self._controller.toolOperationStopped.connect(self._onToolOperationStopped)
        self._build_volume = volume

        self._enabled = True

        self._change_timer = QTimer()
        self._change_timer.setInterval(100)
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self._onChangeTimerFinished)

    def _onSceneChanged(self, source):
        self._change_timer.start()

    def _onChangeTimerFinished(self):
        if not self._enabled:
            return

        root = self._controller.getScene().getRoot()
        for node in BreadthFirstIterator(root):
            if node is root or type(node) is not SceneNode:
                continue

            bbox = node.getBoundingBox()
            if not bbox or not bbox.isValid():
                self._change_timer.start()
                continue

            # Mark the node as outside the build volume if the bounding box test fails.
            if self._build_volume.getBoundingBox().intersectsBox(bbox) != AxisAlignedBox.IntersectionResult.FullIntersection:
                node._outside_buildarea = True
            else:
                node._outside_buildarea = False

            # Move the node upwards if the bottom is below the build platform.
            move_vector = Vector()
            if not Float.fuzzyCompare(bbox.bottom, 0.0):
                move_vector.setY(-bbox.bottom)

            # If there is no convex hull for the node, start calculating it and continue.
            if not node.getDecorator(ConvexHullDecorator):
                node.addDecorator(ConvexHullDecorator())
            
            if not node.callDecoration("getConvexHull"):
                if not node.callDecoration("getConvexHullJob"):
                    job = ConvexHullJob.ConvexHullJob(node)
                    job.start()
                    node.callDecoration("setConvexHullJob", job)

            elif Selection.isSelected(node):
                pass
            else:
                # Check for collisions between convex hulls
                for other_node in BreadthFirstIterator(root):
                    # Ignore root, ourselves and anything that is not a normal SceneNode.
                    if other_node is root or type(other_node) is not SceneNode or other_node is node or other_node in node.getAllChildren() or node in other_node.getAllChildren():
                        continue
                    
                    # Ignore nodes that do not have the right properties set.
                    if not other_node.callDecoration("getConvexHull") or not other_node.getBoundingBox():
                        continue

                    # Check to see if the bounding boxes intersect. If not, we can ignore the node as there is no way the hull intersects.
                    if node.getBoundingBox().intersectsBox(other_node.getBoundingBox()) == AxisAlignedBox.IntersectionResult.NoIntersection:
                        continue

                    # Get the overlap distance for both convex hulls. If this returns None, there is no intersection.
                    overlap = node.callDecoration("getConvexHull").intersectsPolygon(other_node.callDecoration("getConvexHull"))
                    if overlap is None:
                        continue

                    move_vector.setX(overlap[0] * 1.1)
                    move_vector.setZ(overlap[1] * 1.1)
            convex_hull = node.callDecoration("getConvexHull") 
            if convex_hull:
                # Check for collisions between disallowed areas and the object
                for area in self._build_volume.getDisallowedAreas():
                    overlap = convex_hull.intersectsPolygon(area)
                    if overlap is None:
                        continue

                    node._outside_buildarea = True

            if move_vector != Vector():
                op = PlatformPhysicsOperation.PlatformPhysicsOperation(node, move_vector)
                op.push()

    def _onToolOperationStarted(self, tool):
        self._enabled = False

    def _onToolOperationStopped(self, tool):
        self._enabled = True
        self._onChangeTimerFinished()
