# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Scene.SceneNode import SceneNode
from UM.Resources import Resources
from UM.Math.Color import Color
from UM.Math.Vector import Vector
from UM.Mesh.MeshBuilder import MeshBuilder #To create a mesh to display the convex hull with.

from UM.View.GL.OpenGL import OpenGL

class ConvexHullNode(SceneNode):
    def __init__(self, node, hull, parent = None):
        super().__init__(parent)

        self.setCalculateBoundingBox(False)

        self._shader = None

        self._original_parent = parent

        self._inherit_orientation = False
        self._inherit_scale = False

        self._color = Color(35, 35, 35, 128)
        self._mesh_height = 0.1 #The y-coordinate of the convex hull mesh. Must not be 0, to prevent z-fighting.

        self._node = node
        self._node.transformationChanged.connect(self._onNodePositionChanged)
        self._node.parentChanged.connect(self._onNodeParentChanged)
        self._node.decoratorsChanged.connect(self._onNodeDecoratorsChanged)
        self._onNodeDecoratorsChanged(self._node)
        self._convex_hull_head_mesh = None
        self._hull = hull

        hull_points = self._hull.getPoints() # TODO: @UnusedVariable
        hull_mesh = self.createHullMesh(self._hull.getPoints())
        if hull_mesh:
            self.setMeshData(hull_mesh)
        convex_hull_head = self._node.callDecoration("getConvexHullHead")
        if convex_hull_head:
            self._convex_hull_head_mesh = self.createHullMesh(convex_hull_head.getPoints())

    def createHullMesh(self, hull_points):
        #Input checking.
        if len(hull_points) < 3:
            return None

        mesh_builder = MeshBuilder()
        point_first = Vector(hull_points[0][0], self._mesh_height, hull_points[0][1])
        point_previous = Vector(hull_points[1][0], self._mesh_height, hull_points[1][1])
        for point in hull_points[2:]: #Add the faces in the order of a triangle fan.
            point_new = Vector(point[0], self._mesh_height, point[1])
            mesh_builder.addFace(point_first, point_previous, point_new, color = self._color)
            point_previous = point_new #Prepare point_previous for the next triangle.

        return mesh_builder.getData()

    def getWatchedNode(self):
        return self._node

    def render(self, renderer):
        if not self._shader:
            self._shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "default.shader"))
            self._shader.setUniformValue("u_color", self._color)

        if self.getParent():
            renderer.queueNode(self, transparent = True, shader = self._shader, backface_cull = True, sort = -8)
            if self._convex_hull_head_mesh:
                renderer.queueNode(self, shader = self._shader, transparent = True, mesh = self._convex_hull_head_mesh, backface_cull = True, sort = -8)

        return True

    def _onNodePositionChanged(self, node):
        if node.callDecoration("getConvexHull"): 
            node.callDecoration("setConvexHull", None)
            node.callDecoration("setConvexHullNode", None)
            self.setParent(None)

    def _onNodeParentChanged(self, node):
        if node.getParent():
            self.setParent(self._original_parent)
        else:
            self.setParent(None)

    def _onNodeDecoratorsChanged(self, node):
        self._color = Color(35, 35, 35, 0.5)

        if not node:
            return

        if node.hasDecoration("getProfile"):
            self._color.setR(0.75)

        if node.hasDecoration("getSetting"):
            self._color.setG(0.75)
