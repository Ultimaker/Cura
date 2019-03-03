# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import random
from typing import Optional, TYPE_CHECKING

from PyQt5.QtCore import QBuffer

from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Qt.QtApplication import QtApplication
from UM.Math.Vector import Vector
from UM.Math.Color import Color
from UM.Resources import Resources

from UM.View.RenderPass import RenderPass
from UM.View.GL.OpenGL import OpenGL
from UM.View.RenderBatch import RenderBatch

from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator

if TYPE_CHECKING:
    from UM.View.GL.ShaderProgram import ShaderProgram

##  A RenderPass subclass that renders a the distance of selectable objects from the active camera to a texture.
#   The texture is used to map a 2d location (eg the mouse location) to a world space position
#
#   Note that in order to increase precision, the 24 bit depth value is encoded into all three of the R,G & B channels
class PickingPass(RenderPass):
    def __init__(self, width: int, height: int) -> None:
        super().__init__("picking", width, height)

        self._selection_map = {}
        self._renderer = QtApplication.getInstance().getRenderer()

        self._shader = None #type: Optional[ShaderProgram]
        self._scene = QtApplication.getInstance().getController().getScene()

    def render(self) -> None:
        if not self._shader:
            self._shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "camera_distance.shader"))

        width, height = self.getSize()
        self._gl.glViewport(0, 0, width, height)
        self._gl.glClearColor(1.0, 1.0, 1.0, 0.0)
        self._gl.glClear(self._gl.GL_COLOR_BUFFER_BIT | self._gl.GL_DEPTH_BUFFER_BIT)

        # Create a new batch to be rendered
        batch = RenderBatch(self._shader)

        # Fill up the batch with objects that can be sliced. `
        for node in DepthFirstIterator(self._scene.getRoot()): #type: ignore #Ignore type error because iter() should get called automatically by Python syntax.
            if node.callDecoration("isSliceable") and node.getMeshData() and node.isVisible():
                faces = node.getMeshData().getIndices()
                vertices = node.getMeshData().getVertices()
                normals = node.getMeshData().getNormals()
                print("Faces:", faces)
                print("Vertices:", vertices)
                print("Normals:", normals)

                for index, face in enumerate(faces):
                    normal_vertex = normals[face][0]
                    triangle_mesh = vertices[face]
                    print(face, normal_vertex, triangle_mesh)

                    batch.addItem(transformation = node.getWorldTransformation(), mesh = node.getMeshData(), uniforms = { "selection_color": self._getFaceColor(face, normal_vertex)})

        self.bind()
        batch.render(self._scene.getActiveCamera())
        self.release()

    def _getFaceColor(self, face: Vector, normal_vertex: Vector) -> Color:
        while True:
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            a = 255
            color = Color(r, g, b, a)

            if color not in self._selection_map:
                break

        print("Adding color: {color} - {normal}".format(color = color, normal = normal_vertex))
        self._selection_map[color] = {"face": id(face), "normal_vertex": normal_vertex}
        return color

    ##  Get the normal vector at a certain pixel coordinate.
    def getPickedNormalVertex(self, x: int, y: int) -> Optional[Vector]:
        output = self.getOutput()

        print("Creating image")
        output.save("thumbnail.png")

        window_size = self._renderer.getWindowSize()

        px = (0.5 + x / 2.0) * window_size[0]
        py = (0.5 + y / 2.0) * window_size[1]

        if px < 0 or px > (output.width() - 1) or py < 0 or py > (output.height() - 1):
            return None

        pixel = output.pixel(px, py)
        print("######### ", x, y, pixel, Color.fromARGB(pixel))
        face = self._selection_map.get(Color.fromARGB(pixel), None)
        if not face:
            return None
        return face.get("normal_vertex", None)

    ##  Get the distance in mm from the camera to at a certain pixel coordinate.
    def getPickedDepth(self, x: int, y: int) -> float:
        output = self.getOutput()

        window_size = self._renderer.getWindowSize()

        px = (0.5 + x / 2.0) * window_size[0]
        py = (0.5 + y / 2.0) * window_size[1]

        if px < 0 or px > (output.width() - 1) or py < 0 or py > (output.height() - 1):
            return -1

        distance = output.pixel(px, py) # distance in micron, from in r, g & b channels
        distance = (distance & 0x00ffffff) / 1000. # drop the alpha channel and covert to mm
        return distance

    ## Get the world coordinates of a picked point
    def getPickedPosition(self, x: int, y: int) -> Vector:
        distance = self.getPickedDepth(x, y)
        camera = self._scene.getActiveCamera()
        if camera:
            return camera.getRay(x, y).getPointAlongRay(distance)
        return Vector()
