from UM.Mesh.MeshData import MeshData

import numpy
import math

class LayerData(MeshData):
    def __init__(self):
        super().__init__()
        self._layers = {}

    def addPolygon(self, layer, type, data):
        if layer not in self._layers:
            self._layers[layer] = []

        self._layers[layer].append(Polygon(self, type, data))

    def getLayers(self):
        return self._layers

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

        indices = [self._begin + i for i in range(len(data))]

        mesh.addIndices(numpy.array(indices, dtype=numpy.int32))
        self._end = mesh._vertex_count

    @property
    def type(self):
        return self._type

    @property
    def data(self):
        return self._data
