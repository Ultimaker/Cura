# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Mesh.MeshData import MeshData
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Math.Color import Color
from UM.Math.Vector import Vector

import numpy

class LayerData(MeshData):
    def __init__(self):
        super().__init__()
        self._layers = {}
        self._element_counts = {}

    def addLayer(self, layer):
        if layer not in self._layers:
            self._layers[layer] = Layer(layer)

    def addPolygon(self, layer, polygon_type, data, line_width):
        if layer not in self._layers:
            self.addLayer(layer)

        p = Polygon(self, polygon_type, data, line_width)
        self._layers[layer].polygons.append(p)

    def getLayer(self, layer):
        if layer in self._layers:
            return self._layers[layer]

    def getLayers(self):
        return self._layers

    def getElementCounts(self):
        return self._element_counts

    def setLayerHeight(self, layer, height):
        if layer not in self._layers:
            self.addLayer(layer)

        self._layers[layer].setHeight(height)

    def setLayerThickness(self, layer, thickness):
        if layer not in self._layers:
            self.addLayer(layer)

        self._layers[layer].setThickness(thickness)

    def build(self):
        vertex_count = 0
        for layer, data in self._layers.items():
            vertex_count += data.vertexCount()

        vertices = numpy.empty((vertex_count, 3), numpy.float32)
        colors = numpy.empty((vertex_count, 4), numpy.float32)
        indices = numpy.empty((vertex_count, 2), numpy.int32)

        offset = 0
        for layer, data in self._layers.items():
            offset = data.build(offset, vertices, colors, indices)
            self._element_counts[layer] = data.elementCount

        self.clear()
        self.addVertices(vertices)
        self.addColors(colors)
        self.addIndices(indices.flatten())

class Layer():
    def __init__(self, layer_id):
        self._id = layer_id
        self._height = 0.0
        self._thickness = 0.0
        self._polygons = []
        self._element_count = 0

    @property
    def height(self):
        return self._height

    @property
    def thickness(self):
        return self._thickness

    @property
    def polygons(self):
        return self._polygons

    @property
    def elementCount(self):
        return self._element_count

    def setHeight(self, height):
        self._height = height

    def setThickness(self, thickness):
        self._thickness = thickness

    def vertexCount(self):
        result = 0
        for polygon in self._polygons:
            result += polygon.vertexCount()

        return result

    def build(self, offset, vertices, colors, indices):
        result = offset
        for polygon in self._polygons:
            if polygon.type == Polygon.InfillType or polygon.type == Polygon.MoveCombingType or polygon.type == Polygon.MoveRetractionType:
                continue

            polygon.build(result, vertices, colors, indices)
            result += polygon.vertexCount()
            self._element_count += polygon.elementCount

        return result

    def createMesh(self):
        return self.createMeshOrJumps(True)
        
    def createJumps(self):
        return self.createMeshOrJumps(False)
        
    def createMeshOrJumps(self, make_mesh):
        builder = MeshBuilder()

        for polygon in self._polygons:
            if make_mesh and (polygon.type == Polygon.MoveCombingType or polygon.type == Polygon.MoveRetractionType):
                continue
            if not make_mesh and not (polygon.type == Polygon.MoveCombingType or polygon.type == Polygon.MoveRetractionType):
                continue

            poly_color = polygon.getColor()

            points = numpy.copy(polygon.data)
            if polygon.type == Polygon.InfillType or polygon.type == Polygon.SkinType or polygon.type == Polygon.SupportInfillType:
                points[:,1] -= 0.01
            if polygon.type == Polygon.MoveCombingType or polygon.type == Polygon.MoveRetractionType:
                points[:,1] += 0.01

            normals = polygon.getNormals()

            # Scale all by the line width of the polygon so we can easily offset.
            normals *= (polygon.lineWidth / 2)

            #TODO: Use numpy magic to perform the vertex creation to speed up things.
            for i in range(len(points)):
                start = points[i - 1]
                end = points[i]

                normal = normals[i - 1]

                point1 = Vector(data = start - normal)
                point2 = Vector(data = start + normal)
                point3 = Vector(data = end + normal)
                point4 = Vector(data = end - normal)

                builder.addQuad(point1, point2, point3, point4, color = poly_color)

        return builder.getData()

class Polygon():
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
        return ((self._end - self._begin) + 1) * 2 #The range of vertices multiplied by 2 since each vertex is used twice

    @property
    def lineWidth(self):
        return self._line_width

    # Calculate normals for the entire polygon using numpy.
    def getNormals(self):
        normals = numpy.copy(self._data)
        normals[:,1] = 0.0 # We are only interested in 2D normals

        # Calculate the edges between points.
        # The call to numpy.roll shifts the entire array by one so that
        # we end up subtracting each next point from the current, wrapping
        # around. This gives us the edges from the next point to the current
        # point.
        normals[:] = normals[:] - numpy.roll(normals, -1, axis = 0)
        # Calculate the length of each edge using standard Pythagoras
        lengths = numpy.sqrt(normals[:,0] ** 2 + normals[:,2] ** 2)
        # The normal of a 2D vector is equal to its x and y coordinates swapped
        # and then x inverted. This code does that.
        normals[:,[0, 2]] = normals[:,[2, 0]]
        normals[:,0] *= -1

        # Normalize the normals.
        normals[:,0] /= lengths
        normals[:,2] /= lengths

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
