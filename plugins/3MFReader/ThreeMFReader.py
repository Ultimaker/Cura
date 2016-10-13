# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Mesh.MeshReader import MeshReader
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Logger import Logger
from UM.Math.Matrix import Matrix
from UM.Math.Vector import Vector
from UM.Scene.SceneNode import SceneNode
from UM.Scene.GroupDecorator import GroupDecorator
import UM.Application
from UM.Job import Job

from UM.Math.Quaternion import Quaternion

import math
import zipfile

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

##    Base implementation for reading 3MF files. Has no support for textures. Only loads meshes!
class ThreeMFReader(MeshReader):
    def __init__(self):
        super().__init__()
        self._supported_extensions = [".3mf"]
        self._root = None
        self._namespaces = {
            "3mf": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02",
            "cura": "http://software.ultimaker.com/xml/cura/3mf/2015/10"
        }

    def _createNodeFromObject(self, object, name = ""):
        node = SceneNode()
        mesh_builder = MeshBuilder()
        vertex_list = []

        components = object.find(".//3mf:components", self._namespaces)
        if components:
            for component in components:
                id = component.get("objectid")
                new_object = self._root.find("./3mf:resources/3mf:object[@id='{0}']".format(id), self._namespaces)

                new_node = self._createNodeFromObject(new_object)
                node.addChild(new_node)
                transform = component.get("transform")
                if transform is not None:
                    new_node.setTransformation(self._createMatrixFromTransformationString(transform))

        # for vertex in entry.mesh.vertices.vertex:
        for vertex in object.findall(".//3mf:vertex", self._namespaces):
            vertex_list.append([vertex.get("x"), vertex.get("y"), vertex.get("z")])
            Job.yieldThread()

        # If this object has no vertices and just one child, just return the child.
        if len(vertex_list) == 0 and len(node.getChildren()) == 1:
            return node.getChildren()[0]

        if len(node.getChildren()) > 0:
            group_decorator = GroupDecorator()
            node.addDecorator(group_decorator)

        triangles = object.findall(".//3mf:triangle", self._namespaces)
        mesh_builder.reserveFaceCount(len(triangles))

        for triangle in triangles:
            v1 = int(triangle.get("v1"))
            v2 = int(triangle.get("v2"))
            v3 = int(triangle.get("v3"))

            mesh_builder.addFaceByPoints(vertex_list[v1][0], vertex_list[v1][1], vertex_list[v1][2],
                                         vertex_list[v2][0], vertex_list[v2][1], vertex_list[v2][2],
                                         vertex_list[v3][0], vertex_list[v3][1], vertex_list[v3][2])

            Job.yieldThread()

        # Rotate the model; We use a different coordinate frame.
        rotation = Matrix()
        rotation.setByRotationAxis(-0.5 * math.pi, Vector(1, 0, 0))
        flip_matrix = Matrix()

        flip_matrix._data[1, 1] = 0
        flip_matrix._data[1, 2] = 1
        flip_matrix._data[2, 1] = 1
        flip_matrix._data[2, 2] = 0

        # TODO: We currently do not check for normals and simply recalculate them.
        mesh_builder.calculateNormals()
        mesh_builder.setFileName(name)
        mesh_data = mesh_builder.build().getTransformed(flip_matrix)

        if len(mesh_data.getVertices()):
            node.setMeshData(mesh_data)

        node.setSelectable(True)
        return node

    def _createMatrixFromTransformationString(self, transformation):
        splitted_transformation = transformation.split()
        ## Transformation is saved as:
        ## M00 M01 M02 0.0
        ## M10 M11 M12 0.0
        ## M20 M21 M22 0.0
        ## M30 M31 M32 1.0
        ## We switch the row & cols as that is how everyone else uses matrices!
        temp_mat = Matrix()
        # Rotation & Scale
        temp_mat._data[0, 0] = splitted_transformation[0]
        temp_mat._data[1, 0] = splitted_transformation[1]
        temp_mat._data[2, 0] = splitted_transformation[2]
        temp_mat._data[0, 1] = splitted_transformation[3]
        temp_mat._data[1, 1] = splitted_transformation[4]
        temp_mat._data[2, 1] = splitted_transformation[5]
        temp_mat._data[0, 2] = splitted_transformation[6]
        temp_mat._data[1, 2] = splitted_transformation[7]
        temp_mat._data[2, 2] = splitted_transformation[8]

        # Translation
        temp_mat._data[0, 3] = splitted_transformation[9]
        temp_mat._data[1, 3] = splitted_transformation[10]
        temp_mat._data[2, 3] = splitted_transformation[11]

        flip_matrix = Matrix()
        flip_matrix._data[1, 1] = 0
        flip_matrix._data[1, 2] = 1
        flip_matrix._data[2, 1] = 1
        flip_matrix._data[2, 2] = 0
        temp_mat.multiply(flip_matrix)

        return temp_mat

    def read(self, file_name):
        result = SceneNode()
        # The base object of 3mf is a zipped archive.
        archive = zipfile.ZipFile(file_name, "r")
        try:
            self._root = ET.parse(archive.open("3D/3dmodel.model"))

            build_items = self._root.findall("./3mf:build/3mf:item", self._namespaces)

            for build_item in build_items:
                id = build_item.get("objectid")
                object = self._root.find("./3mf:resources/3mf:object[@id='{0}']".format(id), self._namespaces)
                build_item_node = self._createNodeFromObject(object)
                transform = build_item.get("transform")
                if transform is not None:
                    build_item_node.setTransformation(self._createMatrixFromTransformationString(transform))
                result.addChild(build_item_node)

        except Exception as e:
            Logger.log("e", "exception occured in 3mf reader: %s", e)
        try:  # Selftest - There might be more functions that should fail
            bounding_box = result.getBoundingBox()
            bounding_box.isValid()
        except:
            return None

        global_container_stack = UM.Application.getInstance().getGlobalContainerStack()

        if global_container_stack:
            translation = Vector(x=-global_container_stack.getProperty("machine_width", "value") / 2, y=0,
                                 z=global_container_stack.getProperty("machine_depth", "value") / 2)
            result.translate(translation, SceneNode.TransformSpace.World)
        return result
