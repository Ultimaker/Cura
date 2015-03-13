from UM.Mesh.MeshData import MeshData
from UM.Math.Color import Color

import numpy
import math

class LayerData(MeshData):
    def __init__(self):
        super().__init__()
        self._layers = {}
        self._element_counts = []

    def addPolygon(self, layer, type, data):
        if layer not in self._layers:
            self._layers[layer] = []

        p = Polygon(self, type, data)
        self._layers[layer].append(p)
        self._element_counts.append(p.count)

    def getLayers(self):
        return self._layers

    def getElementCounts(self):
        return self._element_counts

class Polygon():
    NoneType = 0
    Inset0Type = 1
    InsetXType = 2
    SkinType = 3
    SupportType = 4
    SkirtType = 5

    def __init__(self, mesh, type, data):
        super().__init__()
        self._type = type
        self._begin = mesh._vertex_count
        mesh.addVertices(data)
        self._end = self._begin + len(data) - 1

        color = None
        if type == self.Inset0Type:
            color = [1, 0, 0, 1]
        elif type == self.InsetXType:
            color = [0, 1, 0, 1]
        elif type == self.SkinType:
            color = [1, 1, 0, 1]
        elif type == self.SupportType:
            color = [0, 1, 1, 1]
        elif type == self.SkirtType:
            color = [0, 1, 1, 1]
        else:
            color = [1, 1, 1, 1]

        colors = [color for i in range(len(data))]
        mesh.addColors(numpy.array(colors, dtype=numpy.float32))

        indices = []
        for i in range(self._begin, self._end):
            indices.append(i)
            indices.append(i + 1)

        indices.append(self._end)
        indices.append(self._begin)
        mesh.addIndices(numpy.array(indices, dtype=numpy.int32))

    @property
    def type(self):
        return self._type

    @property
    def data(self):
        return self._data

    @property
    def count(self):
        return self._end - self._begin
