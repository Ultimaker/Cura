# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import List
import numpy

from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Mesh.MeshData import MeshData
from cura.LayerPolygon import LayerPolygon


class Layer:
    def __init__(self, layer_id: int) -> None:
        self._id = layer_id
        self._height = 0.0
        self._thickness = 0.0
        self._polygons = []  # type: List[LayerPolygon]
        self._vertex_count = 0
        self._element_count = 0

    @property
    def height(self):
        return self._height

    @property
    def thickness(self):
        return self._thickness

    @property
    def polygons(self) -> List[LayerPolygon]:
        return self._polygons

    @property
    def vertexCount(self):
        return self._vertex_count

    @property
    def elementCount(self):
        return self._element_count

    def setHeight(self, height: float) -> None:
        self._height = height

    def setThickness(self, thickness: float) -> None:
        self._thickness = thickness

    def lineMeshVertexCount(self) -> int:
        result = 0
        for polygon in self._polygons:
            result += polygon.lineMeshVertexCount()
        return result

    def lineMeshElementCount(self) -> int:
        result = 0
        for polygon in self._polygons:
            result += polygon.lineMeshElementCount()
        return result

    def lineMeshCumulativeTypeChangeCount(self, path: int) -> int:
        """ The number of line-type changes in this layer up until #path.
        See also LayerPolygon::cumulativeTypeChangeCounts.

        :param path: The path-index up until which the cumulative changes are counted.
        :return: The cumulative number of line-type changes up until this path.
        """
        result = 0
        for polygon in self._polygons:
            num_counts = len(polygon.cumulativeTypeChangeCounts)
            if path < num_counts:
                return result + polygon.cumulativeTypeChangeCounts[path]
            path -= num_counts
            result += polygon.cumulativeTypeChangeCounts[num_counts - 1]
        return result

    def build(self, vertex_offset, index_offset, vertices, colors, line_dimensions, feedrates, extruders, line_types, indices):
        result_vertex_offset = vertex_offset
        result_index_offset = index_offset
        self._vertex_count = 0
        self._element_count = 0
        for polygon in self._polygons:
            polygon.build(result_vertex_offset, result_index_offset, vertices, colors, line_dimensions, feedrates, extruders, line_types, indices)
            result_vertex_offset += polygon.lineMeshVertexCount()
            result_index_offset += polygon.lineMeshElementCount()
            self._vertex_count += polygon.vertexCount
            self._element_count += polygon.elementCount

        return result_vertex_offset, result_index_offset

    def createMesh(self) -> MeshData:
        return self.createMeshOrJumps(True)

    def createJumps(self) -> MeshData:
        return self.createMeshOrJumps(False)

    # Defines the two triplets of local point indices to use to draw the two faces for each line segment in createMeshOrJump
    __index_pattern = numpy.array([[0, 3, 2, 0, 1, 3]], dtype = numpy.int32 )

    def createMeshOrJumps(self, make_mesh: bool) -> MeshData:
        builder = MeshBuilder()

        line_count = 0
        if make_mesh:
            for polygon in self._polygons:
                line_count += polygon.meshLineCount
        else:
            for polygon in self._polygons:
                line_count += polygon.jumpCount

        # Reserve the necessary space for the data upfront
        builder.reserveFaceAndVertexCount(2 * line_count, 4 * line_count)

        for polygon in self._polygons:
            # Filter out the types of lines we are not interested in depending on whether we are drawing the mesh or the jumps.
            index_mask = numpy.logical_not(polygon.jumpMask) if make_mesh else polygon.jumpMask

            # Create an array with rows [p p+1] and only keep those we want to draw based on make_mesh
            points = numpy.concatenate((polygon.data[:-1], polygon.data[1:]), 1)[index_mask.ravel()]
            # Line types of the points we want to draw
            line_types = polygon.types[index_mask]

            # Shift the z-axis according to previous implementation.
            if make_mesh:
                points[polygon.isInfillOrSkinType(line_types), 1::3] -= 0.01
            else:
                points[:, 1::3] += 0.01

            # Create an array with normals and tile 2 copies to match size of points variable
            normals = numpy.tile( polygon.getNormals()[index_mask.ravel()], (1, 2))

            # Scale all normals by the line width of the current line so we can easily offset.
            normals *= (polygon.lineWidths[index_mask.ravel()] / 2)

            # Create 4 points to draw each line segment, points +- normals results in 2 points each.
            # After this we reshape to one point per line.
            f_points = numpy.concatenate((points-normals, points+normals), 1).reshape((-1, 3))

            # __index_pattern defines which points to use to draw the two faces for each lines egment, the following linesegment is offset by 4
            f_indices = ( self.__index_pattern + numpy.arange(0, 4 * len(normals), 4, dtype=numpy.int32).reshape((-1, 1)) ).reshape((-1, 3))
            f_colors = numpy.repeat(polygon.mapLineTypeToColor(line_types), 4, 0)

            builder.addFacesWithColor(f_points, f_indices, f_colors)

        return builder.build()