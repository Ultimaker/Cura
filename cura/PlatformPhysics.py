# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QTimer

from UM.Application import Application
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator
from UM.Math.Vector import Vector
from UM.Scene.Selection import Selection
from UM.Preferences import Preferences

from cura.ConvexHullDecorator import ConvexHullDecorator

from . import PlatformPhysicsOperation
from . import ZOffsetDecorator

import random  # used for list shuffling


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
        self._move_factor = 1.1  # By how much should we multiply overlap to calculate a new spot?
        self._max_overlap_checks = 10  # How many times should we try to find a new spot per tick?

        Preferences.getInstance().addPreference("physics/automatic_push_free", True)
        Preferences.getInstance().addPreference("physics/automatic_drop_down", True)

    def _onSceneChanged(self, source):
        self._change_timer.start()

    def _onChangeTimerFinished(self, was_triggered_by_tool=False):
        if not self._enabled:
            return

        root = self._controller.getScene().getRoot()

        # Keep a list of nodes that are moving. We use this so that we don't move two intersecting objects in the
        # same direction.
        transformed_nodes = []

        # We try to shuffle all the nodes to prevent "locked" situations, where iteration B inverts iteration A.
        # By shuffling the order of the nodes, this might happen a few times, but at some point it will resolve.
        nodes = list(BreadthFirstIterator(root))

        # Only check nodes inside build area.
        nodes = [node for node in nodes if (hasattr(node, "_outside_buildarea") and not node._outside_buildarea)]

        random.shuffle(nodes)
        for node in nodes:
            if node is root or type(node) is not SceneNode or node.getBoundingBox() is None:
                continue

            bbox = node.getBoundingBox()

            # Move it downwards if bottom is above platform
            move_vector = Vector()

            if Preferences.getInstance().getValue("physics/automatic_drop_down") and not (node.getParent() and node.getParent().callDecoration("isGroup")) and node.isEnabled(): #If an object is grouped, don't move it down
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
                    if other_node.getParent() and node.getParent() and (other_node.getParent().callDecoration("isGroup") is not None or node.getParent().callDecoration("isGroup") is not None):
                        continue
                    
                    # Ignore nodes that do not have the right properties set.
                    if not other_node.callDecoration("getConvexHull") or not other_node.getBoundingBox():
                        continue

                    if other_node in transformed_nodes:
                        continue  # Other node is already moving, wait for next pass.

                    overlap = (0, 0)  # Start loop with no overlap
                    current_overlap_checks = 0
                    # Continue to check the overlap until we no longer find one.
                    while overlap and current_overlap_checks < self._max_overlap_checks:
                        current_overlap_checks += 1
                        head_hull = node.callDecoration("getConvexHullHead")
                        if head_hull:  # One at a time intersection.
                            overlap = head_hull.translate(move_vector.x, move_vector.z).intersectsPolygon(other_node.callDecoration("getConvexHull"))
                            if not overlap:
                                other_head_hull = other_node.callDecoration("getConvexHullHead")
                                if other_head_hull:
                                    overlap = node.callDecoration("getConvexHull").translate(move_vector.x, move_vector.z).intersectsPolygon(other_head_hull)
                                    if overlap:
                                        # Moving ensured that overlap was still there. Try anew!
                                        move_vector = move_vector.set(x=move_vector.x + overlap[0] * self._move_factor,
                                                                      z=move_vector.z + overlap[1] * self._move_factor)
                            else:
                                # Moving ensured that overlap was still there. Try anew!
                                move_vector = move_vector.set(x=move_vector.x + overlap[0] * self._move_factor,
                                                              z=move_vector.z + overlap[1] * self._move_factor)
                        else:
                            own_convex_hull = node.callDecoration("getConvexHull")
                            other_convex_hull = other_node.callDecoration("getConvexHull")
                            if own_convex_hull and other_convex_hull:
                                overlap = own_convex_hull.translate(move_vector.x, move_vector.z).intersectsPolygon(other_convex_hull)
                                if overlap:  # Moving ensured that overlap was still there. Try anew!
                                    move_vector = move_vector.set(x=move_vector.x + overlap[0] * self._move_factor,
                                                                  z=move_vector.z + overlap[1] * self._move_factor)
                            else:
                                # This can happen in some cases if the object is not yet done with being loaded.
                                #  Simply waiting for the next tick seems to resolve this correctly.
                                overlap = None

            if not Vector.Null.equals(move_vector, epsilon=1e-5):
                transformed_nodes.append(node)
                op = PlatformPhysicsOperation.PlatformPhysicsOperation(node, move_vector)
                op.push()

        # After moving, we have to evaluate the boundary checks for nodes
        build_volume = Application.getInstance().getBuildVolume()
        build_volume.updateNodeBoundaryCheck()

    def _onToolOperationStarted(self, tool):
        self._enabled = False

    def _onToolOperationStopped(self, tool):
        # Selection tool should not trigger an update.
        if tool.getPluginId() == "SelectionTool":
            return

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
        self._onChangeTimerFinished(True)
