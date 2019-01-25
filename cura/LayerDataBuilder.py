# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from .Layer import Layer
from .LayerPolygon import LayerPolygon
from UM.Mesh.MeshBuilder import MeshBuilder
from .LayerData import LayerData

import numpy
from typing import Dict, Optional


## Builder class for constructing a LayerData object
class LayerDataBuilder(MeshBuilder):
    def __init__(self) -> None:
        super().__init__()
        self._layers = {}  # type: Dict[int, Layer]
        self._element_counts = {}  # type: Dict[int, int]

    def addLayer(self, layer: int) -> None:
        if layer not in self._layers:
            self._layers[layer] = Layer(layer)

    def getLayer(self, layer: int) -> Optional[Layer]:
        return self._layers.get(layer)

    def getLayers(self) -> Dict[int, Layer]:
        return self._layers

    def getElementCounts(self) -> Dict[int, int]:
        return self._element_counts

    def setLayerHeight(self, layer: int, height: float) -> None:
        if layer not in self._layers:
            self.addLayer(layer)

        self._layers[layer].setHeight(height)

    def setLayerThickness(self, layer: int, thickness: float) -> None:
        if layer not in self._layers:
            self.addLayer(layer)

        self._layers[layer].setThickness(thickness)

    ##  Return the layer data as LayerData.
    #
    #   \param material_color_map: [r, g, b, a] for each extruder row.
    #   \param line_type_brightness: compatibility layer view uses line type brightness of 0.5
    def build(self, material_color_map, line_type_brightness = 1.0):
        vertex_count = 0
        index_count = 0
        for layer, data in self._layers.items():
            vertex_count += data.lineMeshVertexCount()
            index_count += data.lineMeshElementCount()

        vertices = numpy.empty((vertex_count, 3), numpy.float32)
        line_dimensions = numpy.empty((vertex_count, 2), numpy.float32)
        colors = numpy.empty((vertex_count, 4), numpy.float32)
        indices = numpy.empty((index_count, 2), numpy.int32)
        feedrates = numpy.empty((vertex_count), numpy.float32)
        extruders = numpy.empty((vertex_count), numpy.float32)
        line_types = numpy.empty((vertex_count), numpy.float32)

        vertex_offset = 0
        index_offset = 0
        for layer, data in sorted(self._layers.items()):
            vertex_offset, index_offset = data.build(vertex_offset, index_offset, vertices, colors, line_dimensions, feedrates, extruders, line_types, indices)
            self._element_counts[layer] = data.elementCount

        self.addVertices(vertices)
        colors[:, 0:3] *= line_type_brightness
        self.addColors(colors)
        self.addIndices(indices.flatten())

        # Note: we're using numpy indexing here.
        # See also: https://docs.scipy.org/doc/numpy/reference/arrays.indexing.html
        material_colors = numpy.zeros((line_dimensions.shape[0], 4), dtype=numpy.float32)
        for extruder_nr in range(material_color_map.shape[0]):
            material_colors[extruders == extruder_nr] = material_color_map[extruder_nr]
        # Set material_colors with indices where line_types (also numpy array) == MoveCombingType
        material_colors[line_types == LayerPolygon.MoveCombingType] = colors[line_types == LayerPolygon.MoveCombingType]
        material_colors[line_types == LayerPolygon.MoveRetractionType] = colors[line_types == LayerPolygon.MoveRetractionType]

        attributes = {
            "line_dimensions": {
                "value": line_dimensions,
                "opengl_name": "a_line_dim",
                "opengl_type": "vector2f"
                },
            "extruders": {
                "value": extruders,
                "opengl_name": "a_extruder",
                "opengl_type": "float"  # Strangely enough, the type has to be float while it is actually an int.
                },
            "colors": {
                "value": material_colors,
                "opengl_name": "a_material_color",
                "opengl_type": "vector4f"
                },
            "line_types": {
                "value": line_types,
                "opengl_name": "a_line_type",
                "opengl_type": "float"
                },
            "feedrates": {
                "value": feedrates,
                "opengl_name": "a_feedrate",
                "opengl_type": "float"
                }
            }

        return LayerData(vertices=self.getVertices(), normals=self.getNormals(), indices=self.getIndices(),
                        colors=self.getColors(), uvs=self.getUVCoordinates(), file_name=self.getFileName(),
                        center_position=self.getCenterPosition(), layers=self._layers,
                        element_counts=self._element_counts, attributes=attributes)
