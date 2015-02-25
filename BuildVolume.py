from UM.Scene.SceneNode import SceneNode
from UM.Application import Application
from UM.Resources import Resources
from UM.Mesh.MeshData import MeshData

class BuildVolume(SceneNode):
    def __init__(self, parent = None):
        super().__init__(parent)

        self._width = 0
        self._height = 0
        self._depth = 0

        self._material = None

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
                Resources.getPath(Resources.ShadersLocation, 'color.frag')
            )
            self._material.setUniformValue('u_color', [0.0, 0.0, 0.5, 0.1])

        renderer.queueNode(self, material = self._material, transparent = True)
        return True

    def rebuild(self):
        if self._width == 0 or self._height == 0 or self._depth == 0:
            return

        mesh = MeshData()

        minW = -self._width / 2
        maxW = self._width / 2
        minH = 0.0
        maxH = self._height
        minD = -self._depth / 2
        maxD = self._depth / 2

        #Front
        mesh.addVertexWithNormal(maxW, maxH, maxD,  0,  0, -1)
        mesh.addVertexWithNormal(minW, minH, maxD,  0,  0, -1)
        mesh.addVertexWithNormal(minW, maxH, maxD,  0,  0, -1)
        mesh.addVertexWithNormal(maxW, maxH, maxD,  0,  0, -1)
        mesh.addVertexWithNormal(maxW, minH, maxD,  0,  0, -1)
        mesh.addVertexWithNormal(minW, minH, maxD,  0,  0, -1)

        #Back
        mesh.addVertexWithNormal(maxW, maxH, minD,  0,  0,  1)
        mesh.addVertexWithNormal(minW, maxH, minD,  0,  0,  1)
        mesh.addVertexWithNormal(minW, minH, minD,  0,  0,  1)
        mesh.addVertexWithNormal(maxW, maxH, minD,  0,  0,  1)
        mesh.addVertexWithNormal(minW, minH, minD,  0,  0,  1)
        mesh.addVertexWithNormal(maxW, minH, minD,  0,  0,  1)

        #Left
        mesh.addVertexWithNormal(minW, maxH, maxD, -1,  0,  0)
        mesh.addVertexWithNormal(minW, minH, minD, -1,  0,  0)
        mesh.addVertexWithNormal(minW, maxH, minD, -1,  0,  0)
        mesh.addVertexWithNormal(minW, maxH, maxD, -1,  0,  0)
        mesh.addVertexWithNormal(minW, minH, maxD, -1,  0,  0)
        mesh.addVertexWithNormal(minW, minH, minD, -1,  0,  0)

        #Right
        mesh.addVertexWithNormal(maxW, maxH, maxD,  1,  0,  0)
        mesh.addVertexWithNormal(maxW, minH, minD,  1,  0,  0)
        mesh.addVertexWithNormal(maxW, minH, maxD,  1,  0,  0)
        mesh.addVertexWithNormal(maxW, maxH, maxD,  1,  0,  0)
        mesh.addVertexWithNormal(maxW, maxH, minD,  1,  0,  0)
        mesh.addVertexWithNormal(maxW, minH, minD,  1,  0,  0)

        #Top
        mesh.addVertexWithNormal(maxW, maxH, maxD,  0, -1,  0)
        mesh.addVertexWithNormal(minW, maxH, maxD,  0, -1,  0)
        mesh.addVertexWithNormal(minW, maxH, minD,  0, -1,  0)
        mesh.addVertexWithNormal(maxW, maxH, maxD,  0, -1,  0)
        mesh.addVertexWithNormal(minW, maxH, minD,  0, -1,  0)
        mesh.addVertexWithNormal(maxW, maxH, minD,  0, -1,  0)

        #Bottom
        mesh.addVertexWithNormal(maxW, minH, maxD,  0,  1,  0)
        mesh.addVertexWithNormal(minW, minH, minD,  0,  1,  0)
        mesh.addVertexWithNormal(minW, minH, maxD,  0,  1,  0)
        mesh.addVertexWithNormal(maxW, minH, maxD,  0,  1,  0)
        mesh.addVertexWithNormal(maxW, minH, minD,  0,  1,  0)
        mesh.addVertexWithNormal(minW, minH, minD,  0,  1,  0)

        self.setMeshData(mesh)
