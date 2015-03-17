from UM.View.Renderer import Renderer
from UM.Scene.SceneNode import SceneNode
from UM.Application import Application
from UM.Resources import Resources
from UM.Mesh.MeshData import MeshData
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Math.Vector import Vector
from UM.Math.Color import Color

import numpy

class BuildVolume(SceneNode):
    VolumeOutlineColor = Color(140, 170, 240, 255)

    def __init__(self, parent = None):
        super().__init__(parent)

        self._width = 0
        self._height = 0
        self._depth = 0

        self._material = None
        self._line_mesh = None

    def setWidth(self, width):
        self._width = width

    def setHeight(self, height):
        self._height = height

    def setDepth(self, depth):
        self._depth = depth

    def render(self, renderer):
        if not self.getMeshData():
            return True
        if self._line_mesh is None:
            return True

        if not self._material:
            self._material = renderer.createMaterial(
                Resources.getPath(Resources.ShadersLocation, 'basic.vert'),
                Resources.getPath(Resources.ShadersLocation, 'vertexcolor.frag')
            )

        #renderer.queueNode(self, material = self._material, transparent = True)
        renderer.queueNode(self, mesh = self._line_mesh, mode = Renderer.RenderLines, material = self._material)
        return True

    def rebuild(self):
        if self._width == 0 or self._height == 0 or self._depth == 0:
            return

        minW = -self._width / 2
        maxW = self._width / 2
        minH = 0.0
        maxH = self._height
        minD = -self._depth / 2
        maxD = self._depth / 2

        md = MeshData()
        md.addVertex(minW, minH, minD)
        md.addVertex(maxW, minH, minD)
        md.addVertex(minW, minH, minD)
        md.addVertex(minW, maxH, minD)
        md.addVertex(minW, maxH, minD)
        md.addVertex(maxW, maxH, minD)
        md.addVertex(maxW, minH, minD)
        md.addVertex(maxW, maxH, minD)

        md.addVertex(minW, minH, maxD)
        md.addVertex(maxW, minH, maxD)
        md.addVertex(minW, minH, maxD)
        md.addVertex(minW, maxH, maxD)
        md.addVertex(minW, maxH, maxD)
        md.addVertex(maxW, maxH, maxD)
        md.addVertex(maxW, minH, maxD)
        md.addVertex(maxW, maxH, maxD)

        md.addVertex(minW, minH, minD)
        md.addVertex(minW, minH, maxD)
        md.addVertex(maxW, minH, minD)
        md.addVertex(maxW, minH, maxD)
        md.addVertex(minW, maxH, minD)
        md.addVertex(minW, maxH, maxD)
        md.addVertex(maxW, maxH, minD)
        md.addVertex(maxW, maxH, maxD)

        for n in range(0, int(maxW), 10):
            md.addVertex(n, minH, minD)
            md.addVertex(n, minH, maxD)

        for n in range(0, int(minW), -10):
            md.addVertex(n, minH, minD)
            md.addVertex(n, minH, maxD)

        for n in range(0, int(maxD), 10):
            md.addVertex(minW, minH, n)
            md.addVertex(maxW, minH, n)

        for n in range(0, int(minD), -10):
            md.addVertex(minW, minH, n)
            md.addVertex(maxW, minH, n)

        for n in range(0, md.getVertexCount()):
            md.setVertexColor(n, BuildVolume.VolumeOutlineColor)

        self._line_mesh = md

        mb = MeshBuilder()

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
