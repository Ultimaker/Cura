from UM.Math.Color import Color

import numpy


class LayerPolygon:
    NoneType = 0
    Inset0Type = 1
    InsetXType = 2
    SkinType = 3
    SupportType = 4
    SkirtType = 5
    InfillType = 6
    SupportInfillType = 7
    MoveCombingType = 8
    MoveRetractionType = 9

    def __init__(self, mesh, polygon_type, data, line_width):
        self._mesh = mesh
        self._type = polygon_type
        self._data = data
        self._line_width = line_width / 1000
        self._begin = 0
        self._end = 0

        self._color = self.__color_map[polygon_type]

    def build(self, offset, vertices, colors, indices):
        self._begin = offset
        self._end = self._begin + len(self._data) - 1

        vertices[self._begin:self._end + 1, :] = self._data[:, :]
        colors[self._begin:self._end + 1, :] = numpy.array([self._color.r * 0.5, self._color.g * 0.5, self._color.b * 0.5, self._color.a], numpy.float32)

        for i in range(self._begin, self._end):
            indices[i, 0] = i
            indices[i, 1] = i + 1

        indices[self._end, 0] = self._end
        indices[self._end, 1] = self._begin

    def getColor(self):
        return self._color

    def vertexCount(self):
        return len(self._data)

    @property
    def type(self):
        return self._type

    @property
    def data(self):
        return self._data

    @property
    def elementCount(self):
        return ((self._end - self._begin) + 1) * 2  # The range of vertices multiplied by 2 since each vertex is used twice

    @property
    def lineWidth(self):
        return self._line_width

    # Calculate normals for the entire polygon using numpy.
    def getNormals(self):
        normals = numpy.copy(self._data)
        normals[:, 1] = 0.0 # We are only interested in 2D normals

        # Calculate the edges between points.
        # The call to numpy.roll shifts the entire array by one so that
        # we end up subtracting each next point from the current, wrapping
        # around. This gives us the edges from the next point to the current
        # point.
        normals[:] = normals[:] - numpy.roll(normals, -1, axis = 0)
        # Calculate the length of each edge using standard Pythagoras
        lengths = numpy.sqrt(normals[:, 0] ** 2 + normals[:, 2] ** 2)
        # The normal of a 2D vector is equal to its x and y coordinates swapped
        # and then x inverted. This code does that.
        normals[:, [0, 2]] = normals[:, [2, 0]]
        normals[:, 0] *= -1

        # Normalize the normals.
        normals[:, 0] /= lengths
        normals[:, 2] /= lengths

        return normals

    __color_map = {
        NoneType: Color(1.0, 1.0, 1.0, 1.0),
        Inset0Type: Color(1.0, 0.0, 0.0, 1.0),
        InsetXType: Color(0.0, 1.0, 0.0, 1.0),
        SkinType: Color(1.0, 1.0, 0.0, 1.0),
        SupportType: Color(0.0, 1.0, 1.0, 1.0),
        SkirtType: Color(0.0, 1.0, 1.0, 1.0),
        InfillType: Color(1.0, 0.74, 0.0, 1.0),
        SupportInfillType: Color(0.0, 1.0, 1.0, 1.0),
        MoveCombingType: Color(0.0, 0.0, 1.0, 1.0),
        MoveRetractionType: Color(0.5, 0.5, 1.0, 1.0),
    }
