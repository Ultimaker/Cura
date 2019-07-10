#Copyright (c) 2019 Ultimaker B.V.
#Cura is released under the terms of the LGPLv3 or higher.

import numpy
import copy
from typing import Optional, Tuple, TYPE_CHECKING

from UM.Math.Polygon import Polygon

if TYPE_CHECKING:
    from UM.Scene.SceneNode import SceneNode

##  Polygon representation as an array for use with Arrange
class ShapeArray:
    def __init__(self, arr: numpy.array, offset_x: float, offset_y: float, scale: float = 1) -> None:
        self.arr = arr
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.scale = scale

    ##  Instantiate from a bunch of vertices
    #   \param vertices
    #   \param scale  scale the coordinates
    @classmethod
    def fromPolygon(cls, vertices: numpy.array, scale: float = 1) -> "ShapeArray":
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
        shape = numpy.array([int(numpy.amax(flip_vertices[:, 0])), int(numpy.amax(flip_vertices[:, 1]))])
        shape[numpy.where(shape == 0)] = 1
        arr = cls.arrayFromPolygon(shape, flip_vertices)
        if not numpy.ndarray.any(arr):
            # set at least 1 pixel
            arr[0][0] = 1
        return cls(arr, offset_x, offset_y)

    ##  Instantiate an offset and hull ShapeArray from a scene node.
    #   \param node source node where the convex hull must be present
    #   \param min_offset offset for the offset ShapeArray
    #   \param scale scale the coordinates
    @classmethod
    def fromNode(cls, node: "SceneNode", min_offset: float, scale: float = 0.5, include_children: bool = False) -> Tuple[Optional["ShapeArray"], Optional["ShapeArray"]]:
        transform = node._transformation
        transform_x = transform._data[0][3]
        transform_y = transform._data[2][3]
        hull_verts = node.callDecoration("getConvexHull")
        # If a model is too small then it will not contain any points
        if hull_verts is None or not hull_verts.getPoints().any():
            return None, None
        # For one_at_a_time printing you need the convex hull head.
        hull_head_verts = node.callDecoration("getConvexHullHead") or hull_verts
        if hull_head_verts is None:
            hull_head_verts = Polygon()

        # If the child-nodes are included, adjust convex hulls as well:
        if include_children:
            children = node.getAllChildren()
            if not children is None:
                for child in children:
                    # 'Inefficient' combination of convex hulls through known code rather than mess it up:
                    child_hull = child.callDecoration("getConvexHull")
                    if not child_hull is None:
                        hull_verts = hull_verts.unionConvexHulls(child_hull)
                    child_hull_head = child.callDecoration("getConvexHullHead") or child_hull
                    if not child_hull_head is None:
                        hull_head_verts = hull_head_verts.unionConvexHulls(child_hull_head)

        offset_verts = hull_head_verts.getMinkowskiHull(Polygon.approximatedCircle(min_offset))
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
    #   \param shape  numpy format shape, [x-size, y-size]
    #   \param vertices
    @classmethod
    def arrayFromPolygon(cls, shape: Tuple[int, int], vertices: numpy.array) -> numpy.array:
        base_array = numpy.zeros(shape, dtype = numpy.int32)  # Initialize your array of zeros

        fill = numpy.ones(base_array.shape) * True  # Initialize boolean array defining shape fill

        # Create check array for each edge segment, combine into fill array
        for k in range(vertices.shape[0]):
            fill = numpy.all([fill, cls._check(vertices[k - 1], vertices[k], base_array)], axis=0)

        # Set all values inside polygon to one
        base_array[fill] = 1

        return base_array

    ##  Return indices that mark one side of the line, used by arrayFromPolygon
    #   Uses the line defined by p1 and p2 to check array of
    #   input indices against interpolated value
    #   Returns boolean array, with True inside and False outside of shape
    #   Originally from: http://stackoverflow.com/questions/37117878/generating-a-filled-polygon-inside-a-numpy-array
    #   \param p1 2-tuple with x, y for point 1
    #   \param p2 2-tuple with x, y for point 2
    #   \param base_array boolean array to project the line on
    @classmethod
    def _check(cls, p1: numpy.array, p2: numpy.array, base_array: numpy.array) -> bool:
        if p1[0] == p2[0] and p1[1] == p2[1]:
            return False
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