# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional

from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Logger import Logger
from UM.Math.Polygon import Polygon
from UM.Math.Vector import Vector
from UM.Scene.SceneNode import SceneNode
from cura.Arranging.ShapeArray import ShapeArray
from cura.BuildVolume import BuildVolume
from cura.Scene import ZOffsetDecorator

from collections import namedtuple

import numpy
import copy

##  Return object for  bestSpot
LocationSuggestion = namedtuple("LocationSuggestion", ["x", "y", "penalty_points", "priority"])


class Arrange:
    """
    The Arrange classed is used together with ShapeArray. Use it to find good locations for objects that you try to put
    on a build place. Different priority schemes can be defined so it alters the behavior while using the same logic.

    Note: Make sure the scale is the same between ShapeArray objects and the Arrange instance.
    """
    build_volume = None  # type: Optional[BuildVolume]

    def __init__(self, x, y, offset_x, offset_y, scale = 0.5):
        self._scale = scale  # convert input coordinates to arrange coordinates
        world_x, world_y = int(x * self._scale), int(y * self._scale)
        self._shape = (world_y, world_x)
        self._priority = numpy.zeros((world_y, world_x), dtype=numpy.int32)  # beware: these are indexed (y, x)
        self._priority_unique_values = []
        self._occupied = numpy.zeros((world_y, world_x), dtype=numpy.int32)  # beware: these are indexed (y, x)
        self._offset_x = int(offset_x * self._scale)
        self._offset_y = int(offset_y * self._scale)
        self._last_priority = 0
        self._is_empty = True

    @classmethod
    def create(cls, scene_root = None, fixed_nodes = None, scale = 0.5, x = 350, y = 250, min_offset = 8):
        """
        Helper to create an Arranger instance

        Either fill in scene_root and create will find all sliceable nodes by itself, or use fixed_nodes to provide the
        nodes yourself.
        :param scene_root: Root for finding all scene nodes
        :param fixed_nodes: Scene nodes to be placed
        :param scale:
        :param x:
        :param y:
        :param min_offset:
        :return:
        """
        arranger = Arrange(x, y, x // 2, y // 2, scale = scale)
        arranger.centerFirst()

        if fixed_nodes is None:
            fixed_nodes = []
            for node_ in DepthFirstIterator(scene_root):
                # Only count sliceable objects
                if node_.callDecoration("isSliceable"):
                    fixed_nodes.append(node_)

        # Place all objects fixed nodes
        for fixed_node in fixed_nodes:
            vertices = fixed_node.callDecoration("getConvexHullHead") or fixed_node.callDecoration("getConvexHull")
            if not vertices:
                continue
            vertices = vertices.getMinkowskiHull(Polygon.approximatedCircle(min_offset))
            points = copy.deepcopy(vertices._points)

            # After scaling (like up to 0.1 mm) the node might not have points
            if not points.size:
                continue

            shape_arr = ShapeArray.fromPolygon(points, scale = scale)
            arranger.place(0, 0, shape_arr)

        # If a build volume was set, add the disallowed areas
        if Arrange.build_volume:
            disallowed_areas = Arrange.build_volume.getDisallowedAreasNoBrim()
            for area in disallowed_areas:
                points = copy.deepcopy(area._points)
                shape_arr = ShapeArray.fromPolygon(points, scale = scale)
                arranger.place(0, 0, shape_arr, update_empty = False)
        return arranger

    ##  This resets the optimization for finding location based on size
    def resetLastPriority(self):
        self._last_priority = 0

    def findNodePlacement(self, node: SceneNode, offset_shape_arr: ShapeArray, hull_shape_arr: ShapeArray, step = 1):
        """
        Find placement for a node (using offset shape) and place it (using hull shape)
        :param node:
        :param offset_shape_arr: hapeArray with offset, for placing the shape
        :param hull_shape_arr: ShapeArray without offset, used to find location
        :param step:
        :return: the nodes that should be placed
        """
        best_spot = self.bestSpot(
            hull_shape_arr, start_prio = self._last_priority, step = step)
        x, y = best_spot.x, best_spot.y

        # Save the last priority.
        self._last_priority = best_spot.priority

        # Ensure that the object is above the build platform
        node.removeDecorator(ZOffsetDecorator.ZOffsetDecorator)
        bbox = node.getBoundingBox()
        if bbox:
            center_y = node.getWorldPosition().y - bbox.bottom
        else:
            center_y = 0

        if x is not None:  # We could find a place
            node.setPosition(Vector(x, center_y, y))
            found_spot = True
            self.place(x, y, offset_shape_arr)  # place the object in arranger
        else:
            Logger.log("d", "Could not find spot!")
            found_spot = False
            node.setPosition(Vector(200, center_y, 100))
        return found_spot

    def centerFirst(self):
        """
        Fill priority, center is best. Lower value is better.
        :return:
        """
        # Square distance: creates a more round shape
        self._priority = numpy.fromfunction(
            lambda j, i: (self._offset_x - i) ** 2 + (self._offset_y - j) ** 2, self._shape, dtype=numpy.int32)
        self._priority_unique_values = numpy.unique(self._priority)
        self._priority_unique_values.sort()

    def backFirst(self):
        """
        Fill priority, back is best. Lower value is better
        :return:
        """
        self._priority = numpy.fromfunction(
            lambda j, i: 10 * j + abs(self._offset_x - i), self._shape, dtype=numpy.int32)
        self._priority_unique_values = numpy.unique(self._priority)
        self._priority_unique_values.sort()

    def checkShape(self, x, y, shape_arr):
        """
        Return the amount of "penalty points" for polygon, which is the sum of priority
        :param x: x-coordinate to check shape
        :param y:
        :param shape_arr: the ShapeArray object to place
        :return: None if occupied
        """
        x = int(self._scale * x)
        y = int(self._scale * y)
        offset_x = x + self._offset_x + shape_arr.offset_x
        offset_y = y + self._offset_y + shape_arr.offset_y
        if offset_x < 0 or offset_y < 0:
            return None  # out of bounds in self._occupied
        occupied_x_max = offset_x + shape_arr.arr.shape[1]
        occupied_y_max = offset_y + shape_arr.arr.shape[0]
        if occupied_x_max > self._occupied.shape[1] + 1 or occupied_y_max > self._occupied.shape[0] + 1:
            return None  # out of bounds in self._occupied
        occupied_slice = self._occupied[
            offset_y:occupied_y_max,
            offset_x:occupied_x_max]
        try:
            if numpy.any(occupied_slice[numpy.where(shape_arr.arr == 1)]):
                return None
        except IndexError:  # out of bounds if you try to place an object outside
            return None
        prio_slice = self._priority[
            offset_y:offset_y + shape_arr.arr.shape[0],
            offset_x:offset_x + shape_arr.arr.shape[1]]
        return numpy.sum(prio_slice[numpy.where(shape_arr.arr == 1)])

    def bestSpot(self, shape_arr, start_prio = 0, step = 1):
        """
        Find "best" spot for ShapeArray
        :param shape_arr:
        :param start_prio: Start with this priority value (and skip the ones before)
        :param step: Slicing value, higher = more skips = faster but less accurate
        :return: namedtuple with properties x, y, penalty_points, priority.
        """
        start_idx_list = numpy.where(self._priority_unique_values == start_prio)
        if start_idx_list:
            try:
                start_idx = start_idx_list[0][0]
            except IndexError:
                start_idx = 0
        else:
            start_idx = 0
        for priority in self._priority_unique_values[start_idx::step]:
            tryout_idx = numpy.where(self._priority == priority)
            for idx in range(len(tryout_idx[0])):
                x = tryout_idx[1][idx]
                y = tryout_idx[0][idx]
                projected_x = int((x - self._offset_x) / self._scale)
                projected_y = int((y - self._offset_y) / self._scale)

                penalty_points = self.checkShape(projected_x, projected_y, shape_arr)
                if penalty_points is not None:
                    return LocationSuggestion(x = projected_x, y = projected_y, penalty_points = penalty_points, priority = priority)
        return LocationSuggestion(x = None, y = None, penalty_points = None, priority = priority)  # No suitable location found :-(

    def place(self, x, y, shape_arr, update_empty = True):
        """
        Place the object.
        Marks the locations in self._occupied and self._priority
        :param x:
        :param y:
        :param shape_arr:
        :param update_empty: updates the _is_empty, used when adding disallowed areas
        :return:
        """
        x = int(self._scale * x)
        y = int(self._scale * y)
        offset_x = x + self._offset_x + shape_arr.offset_x
        offset_y = y + self._offset_y + shape_arr.offset_y
        shape_y, shape_x = self._occupied.shape

        min_x = min(max(offset_x, 0), shape_x - 1)
        min_y = min(max(offset_y, 0), shape_y - 1)
        max_x = min(max(offset_x + shape_arr.arr.shape[1], 0), shape_x - 1)
        max_y = min(max(offset_y + shape_arr.arr.shape[0], 0), shape_y - 1)
        occupied_slice = self._occupied[min_y:max_y, min_x:max_x]
        # we use a slice of shape because it can be out of bounds
        new_occupied = numpy.where(shape_arr.arr[
            min_y - offset_y:max_y - offset_y, min_x - offset_x:max_x - offset_x] == 1)
        if update_empty and new_occupied:
            self._is_empty = False
        occupied_slice[new_occupied] = 1

        # Set priority to low (= high number), so it won't get picked at trying out.
        prio_slice = self._priority[min_y:max_y, min_x:max_x]
        prio_slice[new_occupied] = 999

    @property
    def isEmpty(self):
        return self._is_empty
