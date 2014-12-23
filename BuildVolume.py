from UM.Scene.SceneNode import SceneNode
from UM.Application import Application
from UM.Resources import Resources
from UM.Mesh.MeshData import MeshData

class BuildVolume(SceneNode):
    def __init__(self, parent = None):
        super().__init__(parent)

        mesh = MeshData()

        #Front
        mesh.addVertexWithNormal( 0.5,  0.5,  0.5,  0,  0, -1)
        mesh.addVertexWithNormal(-0.5, -0.5,  0.5,  0,  0, -1)
        mesh.addVertexWithNormal(-0.5,  0.5,  0.5,  0,  0, -1)
        mesh.addVertexWithNormal( 0.5,  0.5,  0.5,  0,  0, -1)
        mesh.addVertexWithNormal( 0.5, -0.5,  0.5,  0,  0, -1)
        mesh.addVertexWithNormal(-0.5, -0.5,  0.5,  0,  0, -1)

        #Back
        mesh.addVertexWithNormal( 0.5,  0.5, -0.5,  0,  0,  1)
        mesh.addVertexWithNormal(-0.5,  0.5, -0.5,  0,  0,  1)
        mesh.addVertexWithNormal(-0.5, -0.5, -0.5,  0,  0,  1)
        mesh.addVertexWithNormal( 0.5,  0.5, -0.5,  0,  0,  1)
        mesh.addVertexWithNormal(-0.5, -0.5, -0.5,  0,  0,  1)
        mesh.addVertexWithNormal( 0.5, -0.5, -0.5,  0,  0,  1)

        #Left
        mesh.addVertexWithNormal(-0.5,  0.5,  0.5, -1,  0,  0)
        mesh.addVertexWithNormal(-0.5, -0.5, -0.5, -1,  0,  0)
        mesh.addVertexWithNormal(-0.5,  0.5, -0.5, -1,  0,  0)
        mesh.addVertexWithNormal(-0.5,  0.5,  0.5, -1,  0,  0)
        mesh.addVertexWithNormal(-0.5, -0.5,  0.5, -1,  0,  0)
        mesh.addVertexWithNormal(-0.5, -0.5, -0.5, -1,  0,  0)

        #Right
        mesh.addVertexWithNormal( 0.5,  0.5,  0.5,  1,  0,  0)
        mesh.addVertexWithNormal( 0.5, -0.5, -0.5,  1,  0,  0)
        mesh.addVertexWithNormal( 0.5, -0.5,  0.5,  1,  0,  0)
        mesh.addVertexWithNormal( 0.5,  0.5,  0.5,  1,  0,  0)
        mesh.addVertexWithNormal( 0.5,  0.5, -0.5,  1,  0,  0)
        mesh.addVertexWithNormal( 0.5, -0.5, -0.5,  1,  0,  0)

        #Top
        mesh.addVertexWithNormal( 0.5,  0.5,  0.5,  0, -1,  0)
        mesh.addVertexWithNormal(-0.5,  0.5,  0.5,  0, -1,  0)
        mesh.addVertexWithNormal(-0.5,  0.5, -0.5,  0, -1,  0)
        mesh.addVertexWithNormal( 0.5,  0.5,  0.5,  0, -1,  0)
        mesh.addVertexWithNormal(-0.5,  0.5, -0.5,  0, -1,  0)
        mesh.addVertexWithNormal( 0.5,  0.5, -0.5,  0, -1,  0)

        #Bottom
        mesh.addVertexWithNormal( 0.5, -0.5,  0.5,  0,  1,  0)
        mesh.addVertexWithNormal(-0.5, -0.5, -0.5,  0,  1,  0)
        mesh.addVertexWithNormal(-0.5, -0.5,  0.5,  0,  1,  0)
        mesh.addVertexWithNormal( 0.5, -0.5,  0.5,  0,  1,  0)
        mesh.addVertexWithNormal( 0.5, -0.5, -0.5,  0,  1,  0)
        mesh.addVertexWithNormal(-0.5, -0.5, -0.5,  0,  1,  0)

        self.setMeshData(mesh)
        self._material = None

    def render(self, renderer):
        if not self._material:
            self._material = renderer.createMaterial(
                Resources.getPath(Resources.ShadersLocation, 'basic.vert'),
                Resources.getPath(Resources.ShadersLocation, 'color.frag')
            )
            self._material.setUniformValue('u_color', [0.5, 0.5, 1.0, 0.5])

        renderer.queueMesh(self.getMeshData(), self.getGlobalTransformation(), material = self._material, transparent = True)
        return True

