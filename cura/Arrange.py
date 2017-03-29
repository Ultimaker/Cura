import numpy as np

##  Some polygon converted to an array
class ShapeArray:
    def __init__(self, arr, offset_x, offset_y, scale = 1):
        self.arr = arr
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.scale = scale

    @classmethod
    def from_polygon(cls, vertices, scale = 1):
        # scale
        vertices = vertices * scale
        # flip y, x -> x, y
        flip_vertices = np.zeros((vertices.shape))
        flip_vertices[:, 0] = vertices[:, 1]
        flip_vertices[:, 1] = vertices[:, 0]
        flip_vertices = flip_vertices[::-1]
        # offset, we want that all coordinates have positive values
        offset_y = int(np.amin(flip_vertices[:, 0]))
        offset_x = int(np.amin(flip_vertices[:, 1]))
        flip_vertices[:, 0] = np.add(flip_vertices[:, 0], -offset_y)
        flip_vertices[:, 1] = np.add(flip_vertices[:, 1], -offset_x)
        shape = [int(np.amax(flip_vertices[:, 0])), int(np.amax(flip_vertices[:, 1]))]
        arr = cls.array_from_polygon(shape, flip_vertices)
        return cls(arr, offset_x, offset_y)

    #   Originally from: http://stackoverflow.com/questions/37117878/generating-a-filled-polygon-inside-a-numpy-array
    @classmethod
    def array_from_polygon(cls, shape, vertices):
        """
        Creates np.array with dimensions defined by shape
        Fills polygon defined by vertices with ones, all other values zero

        Only works correctly for convex hull vertices
        """
        base_array = np.zeros(shape, dtype=float)  # Initialize your array of zeros

        fill = np.ones(base_array.shape) * True  # Initialize boolean array defining shape fill

        # Create check array for each edge segment, combine into fill array
        for k in range(vertices.shape[0]):
            fill = np.all([fill, cls._check(vertices[k - 1], vertices[k], base_array)], axis=0)

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
        idxs = np.indices(base_array.shape)  # Create 3D array of indices

        p1 = p1.astype(float)
        p2 = p2.astype(float)

        if p2[0] == p1[0]:
            sign = np.sign(p2[1] - p1[1])
            return idxs[1] * sign

        if p2[1] == p1[1]:
            sign = np.sign(p2[0] - p1[0])
            return idxs[1] * sign

        # Calculate max column idx for each row idx based on interpolated line between two points

        max_col_idx = (idxs[0] - p1[0]) / (p2[0] - p1[0]) * (p2[1] - p1[1]) + p1[1]
        sign = np.sign(p2[0] - p1[0])
        return idxs[1] * sign <= max_col_idx * sign


class Arrange:
    def __init__(self, x, y, offset_x, offset_y, scale=1):
        self.shape = (y, x)
        self._priority = np.zeros((x, y), dtype=np.int32)
        self._priority_unique_values = []
        self._occupied = np.zeros((x, y), dtype=np.int32)
        self._scale = scale  # convert input coordinates to arrange coordinates
        self._offset_x = offset_x
        self._offset_y = offset_y

    ##  Fill priority, take offset as center. lower is better
    def centerFirst(self):
        #self._priority = np.fromfunction(
        #    lambda i, j: abs(self._offset_x-i)+abs(self._offset_y-j), self.shape)
        self._priority = np.fromfunction(
            lambda i, j: abs(self._offset_x-i)**2+abs(self._offset_y-j)**2, self.shape, dtype=np.int32)
        self._priority_unique_values = np.unique(self._priority)
        self._priority_unique_values.sort()

    ##  Return the amount of "penalty points" for polygon, which is the sum of priority
    #   999999 if occupied
    def check_shape(self, x, y, shape_arr):
        x = int(self._scale * x)
        y = int(self._scale * y)
        offset_x = x + self._offset_x + shape_arr.offset_x
        offset_y = y + self._offset_y + shape_arr.offset_y
        occupied_slice = self._occupied[
            offset_y:offset_y + shape_arr.arr.shape[0],
            offset_x:offset_x + shape_arr.arr.shape[1]]
        try:
            if np.any(occupied_slice[np.where(shape_arr.arr == 1)]):
                return 999999
        except IndexError:  # out of bounds if you try to place an object outside
            return 999999
        prio_slice = self._priority[
            offset_y:offset_y + shape_arr.arr.shape[0],
            offset_x:offset_x + shape_arr.arr.shape[1]]
        return np.sum(prio_slice[np.where(shape_arr.arr == 1)])

    ##  Find "best" spot
    def bestSpot(self, shape_arr, start_prio = 0):
        start_idx_list = np.where(self._priority_unique_values == start_prio)
        if start_idx_list:
            start_idx = start_idx_list[0]
        else:
            start_idx = 0
        for prio in self._priority_unique_values[start_idx:]:
            tryout_idx = np.where(self._priority == prio)
            for idx in range(len(tryout_idx[0])):
                x = tryout_idx[0][idx]
                y = tryout_idx[1][idx]
                projected_x = x - self._offset_x
                projected_y = y - self._offset_y

                # array to "world" coordinates
                penalty_points = self.check_shape(projected_x, projected_y, shape_arr)
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
        occupied_slice[np.where(shape_arr.arr[
            min_y - offset_y:max_y - offset_y, min_x - offset_x:max_x - offset_x] == 1)] = 1

        # Set priority to low (= high number), so it won't get picked at trying out.
        prio_slice = self._priority[min_y:max_y, min_x:max_x]
        prio_slice[np.where(shape_arr.arr[
            min_y - offset_y:max_y - offset_y, min_x - offset_x:max_x - offset_x] == 1)] = 999
