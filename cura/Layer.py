from .LayerPolygon import LayerPolygon

from UM.Math.Vector import Vector
from UM.Mesh.MeshBuilder import MeshBuilder

import numpy

class Layer:
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
            if polygon.type == LayerPolygon.InfillType or polygon.type == LayerPolygon.MoveCombingType or polygon.type == LayerPolygon.MoveRetractionType:
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
            if make_mesh and (polygon.type == LayerPolygon.MoveCombingType or polygon.type == LayerPolygon.MoveRetractionType):
                continue
            if not make_mesh and not (polygon.type == LayerPolygon.MoveCombingType or polygon.type == LayerPolygon.MoveRetractionType):
                continue

            poly_color = polygon.getColor()

            points = numpy.copy(polygon.data)
            if polygon.type == LayerPolygon.InfillType or polygon.type == LayerPolygon.SkinType or polygon.type == LayerPolygon.SupportInfillType:
                points[:,1] -= 0.01
            if polygon.type == LayerPolygon.MoveCombingType or polygon.type == LayerPolygon.MoveRetractionType:
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