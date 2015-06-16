# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Mesh.MeshData import MeshData
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Math.Color import Color
from UM.Math.Vector import Vector

import numpy
import math

class LayerData(MeshData):
    def __init__(self):
        super().__init__()
        self._layers = {}
        self._element_counts = {}

    def addLayer(self, layer):
        if layer not in self._layers:
            self._layers[layer] = Layer(layer)

    def addPolygon(self, layer, type, data, line_width):
        if layer not in self._layers:
            self.addLayer(layer)

        p = Polygon(self, type, data, line_width)
        self._layers[layer].polygons.append(p)

    def getLayer(self, layer):
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
        for layer, data in self._layers.items():
            data.build()

            self._element_counts[layer] = data.elementCount

class Layer():
    def __init__(self, id):
        self._id = id
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

    def build(self):
        for polygon in self._polygons:
            if polygon._type == Polygon.InfillType or polygon._type == Polygon.SupportInfillType:
                continue

            polygon.build()
            self._element_count += polygon.elementCount

class Polygon():
    NoneType = 0
    Inset0Type = 1
    InsetXType = 2
    SkinType = 3
    SupportType = 4
    SkirtType = 5
    InfillType = 6
    SupportInfillType = 7

    def __init__(self, mesh, type, data, line_width):
        super().__init__()
        self._mesh = mesh
        self._type = type
        self._data = data
        self._line_width = line_width / 1000

    def build(self):
        self._begin = self._mesh._vertex_count
        self._mesh.addVertices(self._data)
        self._end = self._begin + len(self._data) - 1

        color = self.getColor()
        color[3] = 2.0

        colors = [color for i in range(len(self._data))]
        self._mesh.addColors(numpy.array(colors, dtype=numpy.float32) * 0.5)

        indices = []
        for i in range(self._begin, self._end):
            indices.append(i)
            indices.append(i + 1)

        indices.append(self._end)
        indices.append(self._begin)
        self._mesh.addIndices(numpy.array(indices, dtype=numpy.int32))

    def getColor(self):
        if self._type == self.Inset0Type:
            return [1.0, 0.0, 0.0, 1.0]
        elif self._type == self.InsetXType:
            return [0.0, 1.0, 0.0, 1.0]
        elif self._type == self.SkinType:
            return [1.0, 1.0, 0.0, 1.0]
        elif self._type == self.SupportType:
            return [0.0, 1.0, 1.0, 1.0]
        elif self._type == self.SkirtType:
            return [0.0, 1.0, 1.0, 1.0]
        elif self._type == self.InfillType:
            return [1.0, 1.0, 0.0, 1.0]
        elif self._type == self.SupportInfillType:
            return [0.0, 1.0, 1.0, 1.0]
        else:
            return [1.0, 1.0, 1.0, 1.0]

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
