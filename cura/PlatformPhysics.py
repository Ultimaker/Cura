# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QTimer

from UM.Application import Application
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator
from UM.Math.Vector import Vector
from UM.Scene.Selection import Selection
from UM.Scene.SceneNodeSettings import SceneNodeSettings

from cura.Scene.ConvexHullDecorator import ConvexHullDecorator

from cura.Operations import PlatformPhysicsOperation
from cura.Scene import ZOffsetDecorator

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
        self._minimum_gap = 2  # It is a minimum distance (in mm) between two models, applicable for small models

        Application.getInstance().getPreferences().addPreference("physics/automatic_push_free", False)
        Application.getInstance().getPreferences().addPreference("physics/automatic_drop_down", True)

    def _onSceneChanged(self, source):
        if not source.callDecoration("isSliceable"):
            return

        self._change_timer.start()

    def _onChangeTimerFinished(self):
        if not self._enabled:
            return

        root = self._controller.getScene().getRoot()

        # Keep a list of nodes that are moving. We use this so that we don't move two intersecting objects in the
        # same direction.
        transformed_nodes = []

        nodes = list(BreadthFirstIterator(root))

        # Only check nodes inside build area.
        nodes = [node for node in nodes if (hasattr(node, "_outside_buildarea") and not node._outside_buildarea)]

        # We try to shuffle all the nodes to prevent "locked" situations, where iteration B inverts iteration A.
        # By shuffling the order of the nodes, this might happen a few times, but at some point it will resolve.
        random.shuffle(nodes)
        for node in nodes:
            if node is root or not isinstance(node, SceneNode) or node.getBoundingBox() is None:
                continue

            bbox = node.getBoundingBox()

            # Move it downwards if bottom is above platform
            move_vector = Vector()

            if Application.getInstance().getPreferences().getValue("physics/automatic_drop_down") and not (node.getParent() and node.getParent().callDecoration("isGroup") or node.getParent() != root) and node.isEnabled(): #If an object is grouped, don't move it down
                z_offset = node.callDecoration("getZOffset") if node.getDecorator(ZOffsetDecorator.ZOffsetDecorator) else 0
                move_vector = move_vector.set(y = -bbox.bottom + z_offset)

            # If there is no convex hull for the node, start calculating it and continue.
            if not node.getDecorator(ConvexHullDecorator) and not node.callDecoration("isNonPrintingMesh"):
                node.addDecorator(ConvexHullDecorator())

            # only push away objects if this node is a printing mesh
            if not node.callDecoration("isNonPrintingMesh") and Application.getInstance().getPreferences().getValue("physics/automatic_push_free"):
                # Do not move locked nodes
                if node.getSetting(SceneNodeSettings.LockPosition):
                    continue

                # Check for collisions between convex hulls
                for other_node in BreadthFirstIterator(root):
                    # Ignore root, ourselves and anything that is not a normal SceneNode.
                    if other_node is root or not issubclass(type(other_node), SceneNode) or other_node is node or other_node.callDecoration("getBuildPlateNumber") != node.callDecoration("getBuildPlateNumber"):
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

                    if other_node.callDecoration("isNonPrintingMesh"):
                        continue

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
                                        move_vector = move_vector.set(x = move_vector.x + overlap[0] * self._move_factor,
                                                                      z = move_vector.z + overlap[1] * self._move_factor)
                            else:
                                # Moving ensured that overlap was still there. Try anew!
                                move_vector = move_vector.set(x = move_vector.x + overlap[0] * self._move_factor,
                                                              z = move_vector.z + overlap[1] * self._move_factor)
                        else:
                            own_convex_hull = node.callDecoration("getConvexHull")
                            other_convex_hull = other_node.callDecoration("getConvexHull")
                            if own_convex_hull and other_convex_hull:
                                overlap = own_convex_hull.translate(move_vector.x, move_vector.z).intersectsPolygon(other_convex_hull)
                                if overlap:  # Moving ensured that overlap was still there. Try anew!
                                    temp_move_vector = move_vector.set(x = move_vector.x + overlap[0] * self._move_factor,
                                                                       z = move_vector.z + overlap[1] * self._move_factor)

                                    # if the distance between two models less than 2mm then try to find a new factor
                                    if abs(temp_move_vector.x - overlap[0]) < self._minimum_gap and abs(temp_move_vector.y - overlap[1]) < self._minimum_gap:
                                        temp_x_factor = (abs(overlap[0]) + self._minimum_gap) / overlap[0] if overlap[0] != 0 else 0 # find x move_factor, like (3.4 + 2) / 3.4 = 1.58
                                        temp_y_factor = (abs(overlap[1]) + self._minimum_gap) / overlap[1] if overlap[1] != 0 else 0 # find y move_factor

                                        temp_scale_factor = temp_x_factor if abs(temp_x_factor) > abs(temp_y_factor) else temp_y_factor

                                        move_vector = move_vector.set(x = move_vector.x + overlap[0] * temp_scale_factor,
                                                                      z = move_vector.z + overlap[1] * temp_scale_factor)
                                    else:
                                        move_vector = temp_move_vector
                            else:
                                # This can happen in some cases if the object is not yet done with being loaded.
                                # Simply waiting for the next tick seems to resolve this correctly.
                                overlap = None

            if not Vector.Null.equals(move_vector, epsilon = 1e-5):
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
        self._onChangeTimerFinished()
