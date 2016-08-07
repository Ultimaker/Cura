# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Mesh.MeshReader import MeshReader
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Logger import Logger
from UM.Math.Matrix import Matrix
from UM.Math.Vector import Vector
from UM.Scene.SceneNode import SceneNode
from UM.Scene.GroupDecorator import GroupDecorator
from UM.Math.Quaternion import Quaternion
from UM.Job import Job

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

        self._namespaces = {
            "3mf": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02",
            "cura": "http://software.ultimaker.com/xml/cura/3mf/2015/10"
        }

    def read(self, file_name):
        result = SceneNode()
        # The base object of 3mf is a zipped archive.
        archive = zipfile.ZipFile(file_name, "r")
        try:
            root = ET.parse(archive.open("3D/3dmodel.model"))

            # There can be multiple objects, try to load all of them.
            objects = root.findall("./3mf:resources/3mf:object", self._namespaces)
            if len(objects) == 0:
                Logger.log("w", "No objects found in 3MF file %s, either the file is corrupt or you are using an outdated format", file_name)
                return None

            for entry in objects:
                mesh_builder = MeshBuilder()
                node = SceneNode()
                vertex_list = []
                #for vertex in entry.mesh.vertices.vertex:
                for vertex in entry.findall(".//3mf:vertex", self._namespaces):
                    vertex_list.append([vertex.get("x"), vertex.get("y"), vertex.get("z")])
                    Job.yieldThread()

                triangles = entry.findall(".//3mf:triangle", self._namespaces)
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

                # TODO: We currently do not check for normals and simply recalculate them.
                mesh_builder.calculateNormals()
                mesh_builder.setFileName(file_name)
                node.setMeshData(mesh_builder.build().getTransformed(rotation))
                node.setSelectable(True)

                transformations = root.findall("./3mf:build/3mf:item[@objectid='{0}']".format(entry.get("id")), self._namespaces)
                transformation = transformations[0] if transformations else None
                if transformation is not None and transformation.get("transform"):
                    splitted_transformation = transformation.get("transform").split()
                    ## Transformation is saved as:
                    ## M00 M01 M02 0.0
                    ## M10 M11 M12 0.0
                    ## M20 M21 M22 0.0
                    ## M30 M31 M32 1.0
                    ## We switch the row & cols as that is how everyone else uses matrices!
                    temp_mat = Matrix()
                    # Rotation & Scale
                    temp_mat._data[0,0] = splitted_transformation[0]
                    temp_mat._data[1,0] = splitted_transformation[1]
                    temp_mat._data[2,0] = splitted_transformation[2]
                    temp_mat._data[0,1] = splitted_transformation[3]
                    temp_mat._data[1,1] = splitted_transformation[4]
                    temp_mat._data[2,1] = splitted_transformation[5]
                    temp_mat._data[0,2] = splitted_transformation[6]
                    temp_mat._data[1,2] = splitted_transformation[7]
                    temp_mat._data[2,2] = splitted_transformation[8]

                    # Translation
                    temp_mat._data[0,3] = splitted_transformation[9]
                    temp_mat._data[1,3] = splitted_transformation[10]
                    temp_mat._data[2,3] = splitted_transformation[11]

                    node.setTransformation(temp_mat)

                result.addChild(node)

                Job.yieldThread()

            # If there is more then one object, group them.
            if len(objects) > 1:
                group_decorator = GroupDecorator()
                result.addDecorator(group_decorator)
            elif len(objects) == 1:
                result = result.getChildren()[0] # Only one object found, return that.
        except Exception as e:
            Logger.log("e", "exception occured in 3mf reader: %s", e)

        try: # Selftest - There might be more functions that should fail
            boundingBox = result.getBoundingBox()
            boundingBox.isValid()
        except:
            return None

        return result
