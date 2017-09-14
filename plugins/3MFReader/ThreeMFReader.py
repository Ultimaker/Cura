# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import os.path
import zipfile

from UM.Job import Job
from UM.Logger import Logger
from UM.Math.Matrix import Matrix
from UM.Math.Vector import Vector
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Mesh.MeshReader import MeshReader
from UM.Scene.GroupDecorator import GroupDecorator
from cura.Settings.SettingOverrideDecorator import SettingOverrideDecorator
from UM.Application import Application
from cura.Settings.ExtruderManager import ExtruderManager
from cura.QualityManager import QualityManager
from UM.Scene.SceneNode import SceneNode
from cura.SliceableObjectDecorator import SliceableObjectDecorator

MYPY = False

import Savitar
import numpy

try:
    if not MYPY:
        import xml.etree.cElementTree as ET
except ImportError:
    Logger.log("w", "Unable to load cElementTree, switching to slower version")
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

    def _createMatrixFromTransformationString(self, transformation):
        if transformation == "":
            return Matrix()

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

    ##  Convenience function that converts a SceneNode object (as obtained from libSavitar) to a Uranium SceneNode.
    #   \returns Uranium SceneNode.
    def _convertSavitarNodeToUMNode(self, savitar_node):
        um_node = SceneNode()
        um_node.setSetting("auto_drop", False)  # Disable the auto-drop feature when loading a project file and processing the nodes for the first time
        transformation = self._createMatrixFromTransformationString(savitar_node.getTransformation())
        um_node.setTransformation(transformation)
        mesh_builder = MeshBuilder()

        data = numpy.fromstring(savitar_node.getMeshData().getFlatVerticesAsBytes(), dtype=numpy.float32)

        vertices = numpy.resize(data, (int(data.size / 3), 3))
        mesh_builder.setVertices(vertices)
        mesh_builder.calculateNormals(fast=True)
        mesh_data = mesh_builder.build()

        if len(mesh_data.getVertices()):
            um_node.setMeshData(mesh_data)

        for child in savitar_node.getChildren():
            child_node = self._convertSavitarNodeToUMNode(child)
            if child_node:
                um_node.addChild(child_node)

        if um_node.getMeshData() is None and len(um_node.getChildren()) == 0:
            return None

        settings = savitar_node.getSettings()

        # Add the setting override decorator, so we can add settings to this node.
        if settings:
            um_node.addDecorator(SettingOverrideDecorator())

            global_container_stack = Application.getInstance().getGlobalContainerStack()
            # Ensure the correct next container for the SettingOverride decorator is set.
            if global_container_stack:
                multi_extrusion = global_container_stack.getProperty("machine_extruder_count", "value") > 1

                # Ensure that all extruder data is reset
                if not multi_extrusion:
                    default_stack_id = global_container_stack.getId()
                else:
                    default_stack = ExtruderManager.getInstance().getExtruderStack(0)
                    if default_stack:
                        default_stack_id = default_stack.getId()
                    else:
                        default_stack_id = global_container_stack.getId()
                um_node.callDecoration("setActiveExtruder", default_stack_id)

                # Get the definition & set it
                definition = QualityManager.getInstance().getParentMachineDefinition(global_container_stack.getBottom())
                um_node.callDecoration("getStack").getTop().setDefinition(definition)

            setting_container = um_node.callDecoration("getStack").getTop()

            for key in settings:
                setting_value = settings[key]

                # Extruder_nr is a special case.
                if key == "extruder_nr":
                    extruder_stack = ExtruderManager.getInstance().getExtruderStack(int(setting_value))
                    if extruder_stack:
                        um_node.callDecoration("setActiveExtruder", extruder_stack.getId())
                    else:
                        Logger.log("w", "Unable to find extruder in position %s", setting_value)
                    continue
                setting_container.setProperty(key,"value", setting_value)

        if len(um_node.getChildren()) > 0:
            group_decorator = GroupDecorator()
            um_node.addDecorator(group_decorator)
        um_node.setSelectable(True)
        if um_node.getMeshData():
            # Assuming that all nodes with mesh data are printable objects
            # affects (auto) slicing
            sliceable_decorator = SliceableObjectDecorator()
            um_node.addDecorator(sliceable_decorator)
        return um_node

    def read(self, file_name):
        result = []
        # The base object of 3mf is a zipped archive.
        try:
            archive = zipfile.ZipFile(file_name, "r")
            self._base_name = os.path.basename(file_name)
            parser = Savitar.ThreeMFParser()
            scene_3mf = parser.parse(archive.open("3D/3dmodel.model").read())
            self._unit = scene_3mf.getUnit()
            for node in scene_3mf.getSceneNodes():
                um_node = self._convertSavitarNodeToUMNode(node)
                if um_node is None:
                    continue
                # compensate for original center position, if object(s) is/are not around its zero position

                transform_matrix = Matrix()
                mesh_data = um_node.getMeshData()
                if mesh_data is not None:
                    extents = mesh_data.getExtents()
                    center_vector = Vector(extents.center.x, extents.center.y, extents.center.z)
                    transform_matrix.setByTranslation(center_vector)
                transform_matrix.multiply(um_node.getLocalTransformation())
                um_node.setTransformation(transform_matrix)

                global_container_stack = Application.getInstance().getGlobalContainerStack()

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
                    translation_vector = Vector(x=-global_container_stack.getProperty("machine_width", "value") / 2,
                                                y=-global_container_stack.getProperty("machine_depth", "value") / 2,
                                                z=0)
                    translation_matrix = Matrix()
                    translation_matrix.setByTranslation(translation_vector)
                    transformation_matrix.multiply(translation_matrix)

                # Third step: 3MF also defines a unit, wheras Cura always assumes mm.
                scale_matrix = Matrix()
                scale_matrix.setByScaleVector(self._getScaleFromUnit(self._unit))
                transformation_matrix.multiply(scale_matrix)

                # Pre multiply the transformation with the loaded transformation, so the data is handled correctly.
                um_node.setTransformation(um_node.getLocalTransformation().preMultiply(transformation_matrix))

                result.append(um_node)

        except Exception:
            Logger.logException("e", "An exception occurred in 3mf reader.")
            return []

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
