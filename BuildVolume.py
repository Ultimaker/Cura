from UM.Scene.SceneNode import SceneNode
from UM.Application import Application
from UM.Resources import Resources
from UM.Mesh.MeshData import MeshData
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Math.Vector import Vector
from UM.Math.Color import Color

class BuildVolume(SceneNode):
    def __init__(self, parent = None):
        super().__init__(parent)

        self._width = 0
        self._height = 0
        self._depth = 0

        self._material = None

        self._grid_mesh = None
        self._grid_material = None

    def setWidth(self, width):
        self._width = width

    def setHeight(self, height):
        self._height = height

    def setDepth(self, depth):
        self._depth = depth

    def render(self, renderer):
        if not self.getMeshData():
            return True

        if not self._material:
            self._material = renderer.createMaterial(
                Resources.getPath(Resources.ShadersLocation, 'basic.vert'),
                Resources.getPath(Resources.ShadersLocation, 'vertexcolor.frag')
            )
            self._grid_material = renderer.createMaterial(
                Resources.getPath(Resources.ShadersLocation, 'basic.vert'),
                Resources.getPath(Resources.ShadersLocation, 'grid.frag')
            )
            self._grid_material.setUniformValue('u_gridColor0', Color(1.0, 1.0, 1.0, 1.0))
            self._grid_material.setUniformValue('u_gridColor1', Color(0.0, 0.0, 0.0, 1.0))

        renderer.queueNode(self, material = self._material, transparent = True)
        renderer.queueNode(self, mesh = self._grid_mesh, material = self._grid_material)
        return True

    def rebuild(self):
        if self._width == 0 or self._height == 0 or self._depth == 0:
            return

        mb = MeshBuilder()

        minW = -self._width / 2
        maxW = self._width / 2
        minH = 0.0
        maxH = self._height
        minD = -self._depth / 2
        maxD = self._depth / 2

        mb.addQuad(
            Vector(minW, minH, maxD),
            Vector(maxW, minH, maxD),
            Vector(maxW, maxH, maxD),
            Vector(minW, maxH, maxD),
            color = Color(0.2, 0.67, 0.9, 0.25),
            normal = Vector(0, 0, -1)
        )

        mb.addQuad(
            Vector(maxW, minH, maxD),
            Vector(maxW, minH, minD),
            Vector(maxW, maxH, minD),
            Vector(maxW, maxH, maxD),
            color = Color(0.2, 0.67, 0.9, 0.38),
            normal = Vector(1, 0, 0)
        )

        mb.addQuad(
            Vector(minW, minH, minD),
            Vector(minW, maxH, minD),
            Vector(maxW, maxH, minD),
            Vector(maxW, minH, minD),
            color = Color(0.2, 0.67, 0.9, 0.25),
            normal = Vector(0, 0, 1)
        )

        mb.addQuad(
            Vector(minW, minH, maxD),
            Vector(minW, maxH, maxD),
            Vector(minW, maxH, minD),
            Vector(minW, minH, minD),
            color = Color(0.2, 0.67, 0.9, 0.38),
            normal = Vector(-1, 0, 0)
        )

        mb.addQuad(
            Vector(minW, maxH, maxD),
            Vector(maxW, maxH, maxD),
            Vector(maxW, maxH, minD),
            Vector(minW, maxH, minD),
            color = Color(0.2, 0.67, 0.9, 0.5),
            normal = Vector(0, -1, 0)
        )

        self.setMeshData(mb.getData())

        mb = MeshBuilder()
        mb.addQuad(
            Vector(minW, minH, maxD),
            Vector(maxW, minH, maxD),
            Vector(maxW, minH, minD),
            Vector(minW, minH, minD)
        )
        self._grid_mesh = mb.getData()
        self._grid_mesh.setVertexUVCoordinates(0, 0.0, 0.0)
        self._grid_mesh.setVertexUVCoordinates(1, 1.0, 1.0)
        self._grid_mesh.setVertexUVCoordinates(2, 0.0, 1.0)
        self._grid_mesh.setVertexUVCoordinates(3, 0.0, 0.0)
        self._grid_mesh.setVertexUVCoordinates(4, 1.0, 1.0)
        self._grid_mesh.setVertexUVCoordinates(5, 1.0, 0.0)
