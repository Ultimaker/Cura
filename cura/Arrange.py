import numpy
from UM.Math.Polygon import Polygon


##  Polygon representation as an array
#
class ShapeArray:
    def __init__(self, arr, offset_x, offset_y, scale = 1):
        self.arr = arr
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.scale = scale

    @classmethod
    def fromPolygon(cls, vertices, scale = 1):
        # scale
        vertices = vertices * scale
        # flip y, x -> x, y
        flip_vertices = numpy.zeros((vertices.shape))
        flip_vertices[:, 0] = vertices[:, 1]
        flip_vertices[:, 1] = vertices[:, 0]
        flip_vertices = flip_vertices[::-1]
        # offset, we want that all coordinates have positive values
        offset_y = int(numpy.amin(flip_vertices[:, 0]))
        offset_x = int(numpy.amin(flip_vertices[:, 1]))
        flip_vertices[:, 0] = numpy.add(flip_vertices[:, 0], -offset_y)
        flip_vertices[:, 1] = numpy.add(flip_vertices[:, 1], -offset_x)
        shape = [int(numpy.amax(flip_vertices[:, 0])), int(numpy.amax(flip_vertices[:, 1]))]
        arr = cls.arrayFromPolygon(shape, flip_vertices)
        return cls(arr, offset_x, offset_y)

    ##  Return an offset and hull ShapeArray from a scenenode.
    @classmethod
    def fromNode(cls, node, min_offset, scale = 0.5):
        # hacky way to undo transformation
        transform = node._transformation
        transform_x = transform._data[0][3]
        transform_y = transform._data[2][3]
        hull_verts = node.callDecoration("getConvexHull")

        offset_verts = hull_verts.getMinkowskiHull(Polygon.approximatedCircle(min_offset))
        offset_points = copy.deepcopy(offset_verts._points)  # x, y
        offset_points[:, 0] = numpy.add(offset_points[:, 0], -transform_x)
        offset_points[:, 1] = numpy.add(offset_points[:, 1], -transform_y)
        offset_shape_arr = ShapeArray.fromPolygon(offset_points, scale = scale)

        hull_points = copy.deepcopy(hull_verts._points)
        hull_points[:, 0] = numpy.add(hull_points[:, 0], -transform_x)
        hull_points[:, 1] = numpy.add(hull_points[:, 1], -transform_y)
        hull_shape_arr = ShapeArray.fromPolygon(hull_points, scale = scale)  # x, y

        return offset_shape_arr, hull_shape_arr


    ##  Create np.array with dimensions defined by shape
    #   Fills polygon defined by vertices with ones, all other values zero
    #   Only works correctly for convex hull vertices
    #   Originally from: http://stackoverflow.com/questions/37117878/generating-a-filled-polygon-inside-a-numpy-array
    @classmethod
    def arrayFromPolygon(cls, shape, vertices):
        base_array = numpy.zeros(shape, dtype=float)  # Initialize your array of zeros

        fill = numpy.ones(base_array.shape) * True  # Initialize boolean array defining shape fill

        # Create check array for each edge segment, combine into fill array
        for k in range(vertices.shape[0]):
            fill = numpy.all([fill, cls._check(vertices[k - 1], vertices[k], base_array)], axis=0)

        # Set all values inside polygon to one
        base_array[fill] = 1

        return base_array

    ##  Return indices that mark one side of the line, used by array_from_polygon
    #   Uses the line defined by p1 and p2 to check array of
    #   input indices against interpolated value
    #   Returns boolean array, with True inside and False outside of shape
    #   Originally from: http://stackoverflow.com/questions/37117878/generating-a-filled-polygon-inside-a-numpy-array
    @classmethod
    def _check(cls, p1, p2, base_array):
        if p1[0] == p2[0] and p1[1] == p2[1]:
            return
        idxs = numpy.indices(base_array.shape)  # Create 3D array of indices

        p1 = p1.astype(float)
        p2 = p2.astype(float)

        if p2[0] == p1[0]:
            sign = numpy.sign(p2[1] - p1[1])
            return idxs[1] * sign

        if p2[1] == p1[1]:
            sign = numpy.sign(p2[0] - p1[0])
            return idxs[1] * sign

        # Calculate max column idx for each row idx based on interpolated line between two points

        max_col_idx = (idxs[0] - p1[0]) / (p2[0] - p1[0]) * (p2[1] - p1[1]) + p1[1]
        sign = numpy.sign(p2[0] - p1[0])
        return idxs[1] * sign <= max_col_idx * sign


from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Logger import Logger
import copy


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
            Logger.log("d", "  # Placing [%s]" % str(fixed_node))

            vertices = fixed_node.callDecoration("getConvexHull")
            points = copy.deepcopy(vertices._points)
            shape_arr = ShapeArray.fromPolygon(points, scale = scale)
            arranger.place(0, 0, shape_arr)
        Logger.log("d", "Current buildplate: \n%s" % str(arranger._occupied[::10, ::10]))
        return arranger

    ##  Find placement for a node and place it
    #
    def findNodePlacements(self, node, offset_shape_arr, hull_shape_arr, count = 1, step = 1):
        # offset_shape_arr, hull_shape_arr, arranger -> nodes, arranger
        nodes = []
        start_prio = 0
        for i in range(count):
            new_node = copy.deepcopy(node)

            Logger.log("d", "  # Finding spot for %s" % new_node)
            x, y, penalty_points, start_prio = self.bestSpot(
                offset_shape_arr, start_prio = start_prio, step = step)
            transformation = new_node._transformation
            if x is not None:  # We could find a place
                transformation._data[0][3] = x
                transformation._data[2][3] = y
                Logger.log("d", "Best place is: %s %s (points = %s)" % (x, y, penalty_points))
                self.place(x, y, hull_shape_arr)  # take place before the next one
                Logger.log("d", "New buildplate: \n%s" % str(self._occupied[::10, ::10]))
            else:
                Logger.log("d", "Could not find spot!")
                transformation._data[0][3] = 200
                transformation._data[2][3] = -100 + i * 20

            nodes.append(new_node)
        return nodes

    ##  Fill priority, take offset as center. lower is better
    def centerFirst(self):
        # Distance x + distance y
        #self._priority = np.fromfunction(
        #    lambda i, j: abs(self._offset_x-i)+abs(self._offset_y-j), self.shape, dtype=np.int32)
        # Square distance
        # self._priority = np.fromfunction(
        #     lambda i, j: abs(self._offset_x-i)**2+abs(self._offset_y-j)**2, self.shape, dtype=np.int32)
        self._priority = numpy.fromfunction(
            lambda i, j: abs(self._offset_x-i)**3+abs(self._offset_y-j)**3, self.shape, dtype=numpy.int32)
        # self._priority = np.fromfunction(
        #    lambda i, j: max(abs(self._offset_x-i), abs(self._offset_y-j)), self.shape, dtype=np.int32)
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
                    return projected_x, projected_y, penalty_points, prio
        return None, None, None, prio  # No suitable location found :-(

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
