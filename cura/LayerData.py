# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.
from .Layer import Layer
from .LayerPolygon import LayerPolygon
from UM.Mesh.MeshData import MeshData

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

        p = LayerPolygon(self, polygon_type, data, line_width)
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
