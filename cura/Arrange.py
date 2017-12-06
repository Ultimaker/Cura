from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Logger import Logger
from UM.Math.Vector import Vector
from cura.ShapeArray import ShapeArray
from cura import ZOffsetDecorator

from collections import namedtuple

import numpy
import copy


##  Return object for  bestSpot
LocationSuggestion = namedtuple("LocationSuggestion", ["x", "y", "penalty_points", "priority"])


##  The Arrange classed is used together with ShapeArray. Use it to find
#   good locations for objects that you try to put on a build place.
#   Different priority schemes can be defined so it alters the behavior while using
#   the same logic.
class Arrange:
    build_volume = None

    def __init__(self, x, y, offset_x, offset_y, scale= 1.0):
        self.shape = (y, x)
        self._priority = numpy.zeros((x, y), dtype=numpy.int32)
        self._priority_unique_values = []
        self._occupied = numpy.zeros((x, y), dtype=numpy.int32)
        self._scale = scale  # convert input coordinates to arrange coordinates
        self._offset_x = offset_x
        self._offset_y = offset_y
        self._last_priority = 0

    ##  Helper to create an Arranger instance
    #
    #   Either fill in scene_root and create will find all sliceable nodes by itself,
    #   or use fixed_nodes to provide the nodes yourself.
    #   \param scene_root   Root for finding all scene nodes
    #   \param fixed_nodes  Scene nodes to be placed
    @classmethod
    def create(cls, scene_root = None, fixed_nodes = None, scale = 0.5):
        arranger = Arrange(220, 220, 110, 110, scale = scale)
        arranger.centerFirst()

        if fixed_nodes is None:
            fixed_nodes = []
            for node_ in DepthFirstIterator(scene_root):
                # Only count sliceable objects
                if node_.callDecoration("isSliceable"):
                    fixed_nodes.append(node_)

        # Place all objects fixed nodes
        for fixed_node in fixed_nodes:
            vertices = fixed_node.callDecoration("getConvexHull")
            if not vertices:
                continue
            points = copy.deepcopy(vertices._points)
            shape_arr = ShapeArray.fromPolygon(points, scale = scale)
            arranger.place(0, 0, shape_arr)

        # If a build volume was set, add the disallowed areas
        if Arrange.build_volume:
            disallowed_areas = Arrange.build_volume.getDisallowedAreas()
            for area in disallowed_areas:
                points = copy.deepcopy(area._points)
                shape_arr = ShapeArray.fromPolygon(points, scale = scale)
                arranger.place(0, 0, shape_arr)
        return arranger

    ##  Find placement for a node (using offset shape) and place it (using hull shape)
    #   return the nodes that should be placed
    #   \param node
    #   \param offset_shape_arr ShapeArray with offset, used to find location
    #   \param hull_shape_arr ShapeArray without offset, for placing the shape
    def findNodePlacement(self, node, offset_shape_arr, hull_shape_arr, step = 1):
        new_node = copy.deepcopy(node)
        best_spot = self.bestSpot(
            offset_shape_arr, start_prio = self._last_priority, step = step)
        x, y = best_spot.x, best_spot.y

        # Save the last priority.
        self._last_priority = best_spot.priority

        # Ensure that the object is above the build platform
        new_node.removeDecorator(ZOffsetDecorator.ZOffsetDecorator)
        if new_node.getBoundingBox():
            center_y = new_node.getWorldPosition().y - new_node.getBoundingBox().bottom
        else:
            center_y = 0

        if x is not None:  # We could find a place
            new_node.setPosition(Vector(x, center_y, y))
            found_spot = True
            self.place(x, y, hull_shape_arr)  # place the object in arranger
        else:
            Logger.log("d", "Could not find spot!"),
            found_spot = False
            new_node.setPosition(Vector(200, center_y, 100))
        return new_node, found_spot

    ##  Fill priority, center is best. Lower value is better
    #   This is a strategy for the arranger.
    def centerFirst(self):
        # Square distance: creates a more round shape
        self._priority = numpy.fromfunction(
            lambda i, j: (self._offset_x - i) ** 2 + (self._offset_y - j) ** 2, self.shape, dtype=numpy.int32)
        self._priority_unique_values = numpy.unique(self._priority)
        self._priority_unique_values.sort()

    ##  Fill priority, back is best. Lower value is better
    #   This is a strategy for the arranger.
    def backFirst(self):
        self._priority = numpy.fromfunction(
            lambda i, j: 10 * j + abs(self._offset_x - i), self.shape, dtype=numpy.int32)
        self._priority_unique_values = numpy.unique(self._priority)
        self._priority_unique_values.sort()

    ##  Return the amount of "penalty points" for polygon, which is the sum of priority
    #   None if occupied
    #   \param x x-coordinate to check shape
    #   \param y y-coordinate
    #   \param shape_arr the ShapeArray object to place
    def checkShape(self, x, y, shape_arr):
        x = int(self._scale * x)
        y = int(self._scale * y)
        offset_x = x + self._offset_x + shape_arr.offset_x
        offset_y = y + self._offset_y + shape_arr.offset_y
        occupied_slice = self._occupied[
            offset_y:offset_y + shape_arr.arr.shape[0],
            offset_x:offset_x + shape_arr.arr.shape[1]]
        try:
            if numpy.any(occupied_slice[numpy.where(shape_arr.arr == 1)]):
                return None
        except IndexError:  # out of bounds if you try to place an object outside
            return None
        prio_slice = self._priority[
            offset_y:offset_y + shape_arr.arr.shape[0],
            offset_x:offset_x + shape_arr.arr.shape[1]]
        return numpy.sum(prio_slice[numpy.where(shape_arr.arr == 1)])

    ##  Find "best" spot for ShapeArray
    #   Return namedtuple with properties x, y, penalty_points, priority
    #   \param shape_arr ShapeArray
    #   \param start_prio Start with this priority value (and skip the ones before)
    #   \param step Slicing value, higher = more skips = faster but less accurate
    def bestSpot(self, shape_arr, start_prio = 0, step = 1):
        start_idx_list = numpy.where(self._priority_unique_values == start_prio)
        if start_idx_list:
            start_idx = start_idx_list[0][0]
        else:
            start_idx = 0
        for priority in self._priority_unique_values[start_idx::step]:
            tryout_idx = numpy.where(self._priority == priority)
            for idx in range(len(tryout_idx[0])):
                x = tryout_idx[0][idx]
                y = tryout_idx[1][idx]
                projected_x = x - self._offset_x
                projected_y = y - self._offset_y

                # array to "world" coordinates
                penalty_points = self.checkShape(projected_x, projected_y, shape_arr)
                if penalty_points is not None:
                    return LocationSuggestion(x = projected_x, y = projected_y, penalty_points = penalty_points, priority = priority)
        return LocationSuggestion(x = None, y = None, penalty_points = None, priority = priority)  # No suitable location found :-(

    ##  Place the object.
    #   Marks the locations in self._occupied and self._priority
    #   \param x x-coordinate
    #   \param y y-coordinate
    #   \param shape_arr ShapeArray object
    def place(self, x, y, shape_arr):
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
        occupied_slice[numpy.where(shape_arr.arr[
            min_y - offset_y:max_y - offset_y, min_x - offset_x:max_x - offset_x] == 1)] = 1

        # Set priority to low (= high number), so it won't get picked at trying out.
        prio_slice = self._priority[min_y:max_y, min_x:max_x]
        prio_slice[numpy.where(shape_arr.arr[
            min_y - offset_y:max_y - offset_y, min_x - offset_x:max_x - offset_x] == 1)] = 999
