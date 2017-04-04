from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Logger import Logger
from cura.ShapeArray import ShapeArray

from collections import namedtuple

import numpy
import copy


##  Return object for  bestSpot
LocationSuggestion = namedtuple("LocationSuggestion", ["x", "y", "penalty_points", "priority"])

##  The Arrange classed is used together with ShapeArray. The class tries to find
#   good locations for objects that you try to put on a build place.
#   Different priority schemes can be defined so it alters the behavior while using
#   the same logic.
class Arrange:
    def __init__(self, x, y, offset_x, offset_y, scale=1):
        self.shape = (y, x)
        self._priority = numpy.zeros((x, y), dtype=numpy.int32)
        self._priority_unique_values = []
        self._occupied = numpy.zeros((x, y), dtype=numpy.int32)
        self._scale = scale  # convert input coordinates to arrange coordinates
        self._offset_x = offset_x
        self._offset_y = offset_y

    ##  Helper to create an Arranger instance
    #
    #   Either fill in scene_root and create will find all sliceable nodes by itself,
    #   or use fixed_nodes to provide the nodes yourself.
    #   \param scene_root
    #   \param fixed_nodes
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
        # place all objects fixed nodes
        for fixed_node in fixed_nodes:
            vertices = fixed_node.callDecoration("getConvexHull")
            points = copy.deepcopy(vertices._points)
            shape_arr = ShapeArray.fromPolygon(points, scale = scale)
            arranger.place(0, 0, shape_arr)
        return arranger

    ##  Find placement for a node (using offset shape) and place it (using hull shape)
    #   return the nodes that should be placed
    def findNodePlacements(self, node, offset_shape_arr, hull_shape_arr, count = 1, step = 1):
        nodes = []
        start_prio = 0
        for i in range(count):
            new_node = copy.deepcopy(node)

            best_spot = self.bestSpot(
                offset_shape_arr, start_prio = start_prio, step = step)
            x, y = best_spot.x, best_spot.y
            start_prio = best_spot.priority
            transformation = new_node._transformation
            if x is not None:  # We could find a place
                transformation._data[0][3] = x
                transformation._data[2][3] = y
                self.place(x, y, hull_shape_arr)  # take place before the next one
            else:
                Logger.log("d", "Could not find spot!")
                transformation._data[0][3] = 200
                transformation._data[2][3] = 100 + i * 20

            nodes.append(new_node)
        return nodes

    ##  Fill priority, take offset as center. lower is better
    def centerFirst(self):
        # Distance x + distance y: creates diamond shape
        #self._priority = numpy.fromfunction(
        #    lambda i, j: abs(self._offset_x-i)+abs(self._offset_y-j), self.shape, dtype=numpy.int32)
        # Square distance: creates a more round shape
        self._priority = numpy.fromfunction(
            lambda i, j: (self._offset_x - i) ** 2 + (self._offset_y - j) ** 2, self.shape, dtype=numpy.int32)
        self._priority_unique_values = numpy.unique(self._priority)
        self._priority_unique_values.sort()

    ##
    def backFirst(self):
        self._priority = numpy.fromfunction(
            lambda i, j: 10 * j + abs(self._offset_x - i), self.shape, dtype=numpy.int32)
        self._priority_unique_values = numpy.unique(self._priority)
        self._priority_unique_values.sort()

    ##  Return the amount of "penalty points" for polygon, which is the sum of priority
    #   999999 if occupied
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
                return 999999
        except IndexError:  # out of bounds if you try to place an object outside
            return 999999
        prio_slice = self._priority[
            offset_y:offset_y + shape_arr.arr.shape[0],
            offset_x:offset_x + shape_arr.arr.shape[1]]
        return numpy.sum(prio_slice[numpy.where(shape_arr.arr == 1)])

    ##  Find "best" spot for ShapeArray
    #   Return namedtuple with properties x, y, penalty_points, priority
    def bestSpot(self, shape_arr, start_prio = 0, step = 1):
        start_idx_list = numpy.where(self._priority_unique_values == start_prio)
        if start_idx_list:
            start_idx = start_idx_list[0]
        else:
            start_idx = 0
        for prio in self._priority_unique_values[start_idx::step]:
            tryout_idx = numpy.where(self._priority == prio)
            for idx in range(len(tryout_idx[0])):
                x = tryout_idx[0][idx]
                y = tryout_idx[1][idx]
                projected_x = x - self._offset_x
                projected_y = y - self._offset_y

                # array to "world" coordinates
                penalty_points = self.checkShape(projected_x, projected_y, shape_arr)
                if penalty_points != 999999:
                    return LocationSuggestion(x = projected_x, y = projected_y, penalty_points = penalty_points, priority = prio)
        return LocationSuggestion(x = None, y = None, penalty_points = None, priority = prio)  # No suitable location found :-(

    ##  Place the object
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
