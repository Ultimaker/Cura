# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import QTimer

from UM.Scene.SceneNode import SceneNode
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator
from UM.Math.Vector import Vector
from UM.Math.AxisAlignedBox import AxisAlignedBox
from UM.Scene.Selection import Selection
from UM.Preferences import Preferences

from cura.ConvexHullDecorator import ConvexHullDecorator

from . import PlatformPhysicsOperation
from . import ZOffsetDecorator

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

        Preferences.getInstance().addPreference("physics/automatic_push_free", True)

    def _onSceneChanged(self, source):
        self._change_timer.start()

    def _onChangeTimerFinished(self):
        if not self._enabled:
            return

        root = self._controller.getScene().getRoot()

        for node in BreadthFirstIterator(root):
            if node is root or type(node) is not SceneNode or node.getBoundingBox() is None:
                continue

            bbox = node.getBoundingBox()

            # Ignore intersections with the bottom
            build_volume_bounding_box = self._build_volume.getBoundingBox()
            if build_volume_bounding_box:
                # It's over 9000!
                build_volume_bounding_box = build_volume_bounding_box.set(bottom=-9001)
            else:
                # No bounding box. This is triggered when running Cura from command line with a model for the first time
                # In that situation there is a model, but no machine (and therefore no build volume.
                return
            node._outside_buildarea = False

            # Mark the node as outside the build volume if the bounding box test fails.
            if build_volume_bounding_box.intersectsBox(bbox) != AxisAlignedBox.IntersectionResult.FullIntersection:
                node._outside_buildarea = True

            # Move it downwards if bottom is above platform
            move_vector = Vector()
            if not (node.getParent() and node.getParent().callDecoration("isGroup")): #If an object is grouped, don't move it down
                z_offset = node.callDecoration("getZOffset") if node.getDecorator(ZOffsetDecorator.ZOffsetDecorator) else 0
                move_vector = move_vector.set(y=-bbox.bottom + z_offset)

            # If there is no convex hull for the node, start calculating it and continue.
            if not node.getDecorator(ConvexHullDecorator):
                node.addDecorator(ConvexHullDecorator())

            if Preferences.getInstance().getValue("physics/automatic_push_free"):
                # Check for collisions between convex hulls
                for other_node in BreadthFirstIterator(root):
                    # Ignore root, ourselves and anything that is not a normal SceneNode.
                    if other_node is root or type(other_node) is not SceneNode or other_node is node:
                        continue
                    
                    # Ignore collisions of a group with it's own children
                    if other_node in node.getAllChildren() or node in other_node.getAllChildren():
                        continue
                    
                    # Ignore collisions within a group
                    if other_node.getParent().callDecoration("isGroup") is not None or node.getParent().callDecoration("isGroup") is not None:
                        continue
                    
                    # Ignore nodes that do not have the right properties set.
                    if not other_node.callDecoration("getConvexHull") or not other_node.getBoundingBox():
                        continue

                    # Get the overlap distance for both convex hulls. If this returns None, there is no intersection.
                    head_hull = node.callDecoration("getConvexHullHead")
                    if head_hull:
                        overlap = head_hull.intersectsPolygon(other_node.callDecoration("getConvexHullHead"))
                        if not overlap:
                            other_head_hull = other_node.callDecoration("getConvexHullHead")
                            if other_head_hull:
                                overlap = node.callDecoration("getConvexHullHead").intersectsPolygon(other_head_hull)
                    else:
                        own_convex_hull = node.callDecoration("getConvexHull")
                        other_convex_hull = other_node.callDecoration("getConvexHull")
                        if own_convex_hull and other_convex_hull:
                            overlap = own_convex_hull.intersectsPolygon(other_convex_hull)
                        else:
                            # This can happen in some cases if the object is not yet done with being loaded.
                            #  Simply waiting for the next tick seems to resolve this correctly.
                            overlap = None

                    if overlap is None:
                        continue
                    move_vector = move_vector.set(x=overlap[0] * 1.1, z=overlap[1] * 1.1)
            convex_hull = node.callDecoration("getConvexHull")
            if convex_hull:
                if not convex_hull.isValid():
                    return
                # Check for collisions between disallowed areas and the object
                for area in self._build_volume.getDisallowedAreas():
                    overlap = convex_hull.intersectsPolygon(area)
                    if overlap is None:
                        continue

                    node._outside_buildarea = True

            if not Vector.Null.equals(move_vector, epsilon=1e-5):
                op = PlatformPhysicsOperation.PlatformPhysicsOperation(node, move_vector)
                op.push()

    def _onToolOperationStarted(self, tool):
        self._enabled = False

    def _onToolOperationStopped(self, tool):
        if tool.getPluginId() == "TranslateTool":
            for node in Selection.getAllSelectedObjects():
                if node.getBoundingBox().bottom < 0:
                    if not node.getDecorator(ZOffsetDecorator.ZOffsetDecorator):
                        node.addDecorator(ZOffsetDecorator.ZOffsetDecorator())

                    node.callDecoration("setZOffset", node.getBoundingBox().bottom)
                else:
                    if node.getDecorator(ZOffsetDecorator.ZOffsetDecorator):
                        node.removeDecorator(ZOffsetDecorator.ZOffsetDecorator)

        self._enabled = True
        self._onChangeTimerFinished()
