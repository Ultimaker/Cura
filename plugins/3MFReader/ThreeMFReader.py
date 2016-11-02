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


import os.path
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
        self._base_name = ""
        self._unit = None

    def _createNodeFromObject(self, object, name = ""):
        node = SceneNode()
        node.setName(name)
        mesh_builder = MeshBuilder()
        vertex_list = []

        components = object.find(".//3mf:components", self._namespaces)
        if components:
            for component in components:
                id = component.get("objectid")
                new_object = self._root.find("./3mf:resources/3mf:object[@id='{0}']".format(id), self._namespaces)
                new_node = self._createNodeFromObject(new_object, self._base_name + "_" + str(id))
                node.addChild(new_node)
                transform = component.get("transform")
                if transform is not None:
                    new_node.setTransformation(self._createMatrixFromTransformationString(transform))

        # for vertex in entry.mesh.vertices.vertex:
        for vertex in object.findall(".//3mf:vertex", self._namespaces):
            vertex_list.append([vertex.get("x"), vertex.get("y"), vertex.get("z")])
            Job.yieldThread()

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

        # TODO: We currently do not check for normals and simply recalculate them.
        mesh_builder.calculateNormals()
        mesh_builder.setFileName(name)
        mesh_data = mesh_builder.build()

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

        return temp_mat

    def read(self, file_name):
        result = SceneNode()
        group_decorator = GroupDecorator()
        result.addDecorator(group_decorator)
        # The base object of 3mf is a zipped archive.
        archive = zipfile.ZipFile(file_name, "r")
        self._base_name = os.path.basename(file_name)
        try:
            self._root = ET.parse(archive.open("3D/3dmodel.model"))
            self._unit = self._root.getroot().get("unit")

            build_items = self._root.findall("./3mf:build/3mf:item", self._namespaces)

            for build_item in build_items:
                id = build_item.get("objectid")
                object = self._root.find("./3mf:resources/3mf:object[@id='{0}']".format(id), self._namespaces)
                if "type" in object.attrib:
                    if object.attrib["type"] == "support" or object.attrib["type"] == "other":
                        # Ignore support objects, as cura does not support these.
                        # We can't guarantee that they wont be made solid.
                        # We also ignore "other", as I have no idea what to do with them.
                        Logger.log("w", "3MF file contained an object of type %s which is not supported by Cura", object.attrib["type"])
                        continue
                    elif object.attrib["type"] == "solidsupport" or object.attrib["type"] == "model":
                        pass  # Load these as normal
                    else:
                        # We should technically fail at this point because it's an invalid 3MF, but try to continue anyway.
                        Logger.log("e", "3MF file contained an object of type %s which is not supported by the 3mf spec",
                                   object.attrib["type"])
                        continue

                build_item_node = self._createNodeFromObject(object, self._base_name + "_" + str(id))
                transform = build_item.get("transform")
                if transform is not None:
                    build_item_node.setTransformation(self._createMatrixFromTransformationString(transform))
                global_container_stack = UM.Application.getInstance().getGlobalContainerStack()

                # Create a transformation Matrix to convert from 3mf worldspace into ours.
                # First step: flip the y and z axis.
                transformation_matrix = Matrix()
                transformation_matrix._data[1, 1] = 0
                transformation_matrix._data[1, 2] = 1
                transformation_matrix._data[2, 1] = -1
                transformation_matrix._data[2, 2] = 0

                # Second step: 3MF defines the left corner of the machine as center, whereas cura uses the center of the
                # build volume.
                if global_container_stack:
                    translation_vector = Vector(x = -global_container_stack.getProperty("machine_width", "value") / 2,
                                                y = -global_container_stack.getProperty("machine_depth", "value") / 2,
                                                z = 0)
                    translation_matrix = Matrix()
                    translation_matrix.setByTranslation(translation_vector)
                    transformation_matrix.multiply(translation_matrix)

                # Third step: 3MF also defines a unit, wheras Cura always assumes mm.
                scale_matrix = Matrix()
                scale_matrix.setByScaleVector(self._getScaleFromUnit(self._unit))
                transformation_matrix.multiply(scale_matrix)

                # Pre multiply the transformation with the loaded transformation, so the data is handled correctly.
                build_item_node.setTransformation(build_item_node.getLocalTransformation().preMultiply(transformation_matrix))

                result.addChild(build_item_node)

        except Exception as e:
            Logger.log("e", "exception occured in 3mf reader: %s", e)
        try:  # Selftest - There might be more functions that should fail
            bounding_box = result.getBoundingBox()
            bounding_box.isValid()
        except:
            return None


        result.setEnabled(False) # The result should not be moved in any way, so disable it.
        return result

    ##  Create a scale vector based on a unit string.
    #   The core spec defines the following:
    #   * micron
    #   * millimeter (default)
    #   * centimeter
    #   * inch
    #   * foot
    #   * meter
    def _getScaleFromUnit(self, unit):
        if unit is None:
            unit = "millimeter"
        if unit == "micron":
            scale = 0.001
        elif unit == "millimeter":
            scale = 1
        elif unit == "centimeter":
            scale = 10
        elif unit == "inch":
            scale = 25.4
        elif unit == "foot":
            scale = 304.8
        elif unit == "meter":
            scale = 1000
        else:
            Logger.log("w", "Unrecognised unit %s used. Assuming mm instead", unit)
            scale = 1

        return Vector(scale, scale, scale)