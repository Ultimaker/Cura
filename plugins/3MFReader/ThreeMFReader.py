#  Copyright (c) 2021-2022 Ultimaker B.V.
#  Cura is released under the terms of the LGPLv3 or higher.

import os.path
import zipfile
from typing import List, Optional, Union, TYPE_CHECKING, cast

import pySavitar as Savitar
import numpy

from UM.Logger import Logger
from UM.Math.Matrix import Matrix
from UM.Math.Vector import Vector
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Mesh.MeshReader import MeshReader
from UM.MimeTypeDatabase import MimeTypeDatabase, MimeType
from UM.Scene.GroupDecorator import GroupDecorator
from UM.Scene.SceneNode import SceneNode  # For typing.
from UM.Scene.SceneNodeSettings import SceneNodeSettings
from UM.Util import parseBool
from cura.CuraApplication import CuraApplication
from cura.Machines.ContainerTree import ContainerTree
from cura.Scene.BuildPlateDecorator import BuildPlateDecorator
from cura.Scene.ConvexHullDecorator import ConvexHullDecorator
from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator
from cura.Scene.ZOffsetDecorator import ZOffsetDecorator
from cura.Settings.ExtruderManager import ExtruderManager

try:
    if not TYPE_CHECKING:
        import xml.etree.cElementTree as ET
except ImportError:
    Logger.log("w", "Unable to load cElementTree, switching to slower version")
    import xml.etree.ElementTree as ET


class ThreeMFReader(MeshReader):
    """Base implementation for reading 3MF files. Has no support for textures. Only loads meshes!"""

    def __init__(self) -> None:
        super().__init__()

        MimeTypeDatabase.addMimeType(
            MimeType(
                name="application/vnd.ms-package.3dmanufacturing-3dmodel+xml",
                comment="3MF",
                suffixes=["3mf"]
            )
        )

        self._supported_extensions = [".3mf"]
        self._root = None
        self._base_name = ""
        self._unit = None
        self._empty_project = False

    def emptyFileHintSet(self) -> bool:
        return self._empty_project

    @staticmethod
    def _createMatrixFromTransformationString(transformation: str) -> Matrix:
        if transformation == "":
            return Matrix()

        split_transformation = transformation.split()
        temp_mat = Matrix()
        """Transformation is saved as:
            M00 M01 M02 0.0

            M10 M11 M12 0.0

            M20 M21 M22 0.0

            M30 M31 M32 1.0
        We switch the row & cols as that is how everyone else uses matrices!
        """
        # Rotation & Scale
        temp_mat._data[0, 0] = split_transformation[0]
        temp_mat._data[1, 0] = split_transformation[1]
        temp_mat._data[2, 0] = split_transformation[2]
        temp_mat._data[0, 1] = split_transformation[3]
        temp_mat._data[1, 1] = split_transformation[4]
        temp_mat._data[2, 1] = split_transformation[5]
        temp_mat._data[0, 2] = split_transformation[6]
        temp_mat._data[1, 2] = split_transformation[7]
        temp_mat._data[2, 2] = split_transformation[8]

        # Translation
        temp_mat._data[0, 3] = split_transformation[9]
        temp_mat._data[1, 3] = split_transformation[10]
        temp_mat._data[2, 3] = split_transformation[11]

        return temp_mat

    @staticmethod
    def _convertSavitarNodeToUMNode(savitar_node: Savitar.SceneNode, file_name: str = "", archive: zipfile.ZipFile = None) -> Optional[SceneNode]:
        """Convenience function that converts a SceneNode object (as obtained from libSavitar) to a scene node.

        :returns: Scene node.
        """
        try:
            node_name = savitar_node.getName()
            node_id = savitar_node.getId()
        except AttributeError:
            Logger.log("e", "Outdated version of libSavitar detected! Please update to the newest version!")
            node_name = ""
            node_id = ""

        if node_name == "":
            if file_name != "":
                node_name = os.path.basename(file_name)
            else:
                node_name = "Object {}".format(node_id)

        active_build_plate = CuraApplication.getInstance().getMultiBuildPlateModel().activeBuildPlate

        component_path = savitar_node.getComponentPath()
        if component_path != "" and archive is not None:
            savitar_node.parseComponentData(archive.open(component_path.lstrip("/")).read())

        um_node = CuraSceneNode() # This adds a SettingOverrideDecorator
        um_node.addDecorator(BuildPlateDecorator(active_build_plate))
        try:
            um_node.addDecorator(ConvexHullDecorator())
        except:
            pass
        um_node.setName(node_name)
        um_node.setId(node_id)
        transformation = ThreeMFReader._createMatrixFromTransformationString(savitar_node.getTransformation())
        um_node.setTransformation(transformation)
        mesh_builder = MeshBuilder()

        data = numpy.fromstring(savitar_node.getMeshData().getFlatVerticesAsBytes(), dtype=numpy.float32)

        vertices = numpy.resize(data, (int(data.size / 3), 3))
        mesh_builder.setVertices(vertices)
        mesh_builder.calculateNormals(fast=True)
        mesh_builder.setMeshId(node_id)
        if file_name:
            # The filename is used to give the user the option to reload the file if it is changed on disk
            # It is only set for the root node of the 3mf file
            mesh_builder.setFileName(file_name)
        mesh_data = mesh_builder.build()

        if len(mesh_data.getVertices()):
            um_node.setMeshData(mesh_data)

        for child in savitar_node.getChildren():
            child_node = ThreeMFReader._convertSavitarNodeToUMNode(child, archive=archive)
            if child_node:
                um_node.addChild(child_node)

        if um_node.getMeshData() is None and len(um_node.getChildren()) == 0:
            return None

        settings = savitar_node.getSettings()

        # Add the setting override decorator, so we can add settings to this node.
        if settings:
            global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()

            # Ensure the correct next container for the SettingOverride decorator is set.
            if global_container_stack:
                default_stack = ExtruderManager.getInstance().getExtruderStack(0)

                if default_stack:
                    um_node.callDecoration("setActiveExtruder", default_stack.getId())

                # Get the definition & set it
                definition_id = ContainerTree.getInstance().machines[global_container_stack.definition.getId()].quality_definition
                um_node.callDecoration("getStack").getTop().setDefinition(definition_id)

            setting_container = um_node.callDecoration("getStack").getTop()
            known_setting_keys = um_node.callDecoration("getStack").getAllKeys()
            for key in settings:
                setting_value = settings[key].value

                # Extruder_nr is a special case.
                if key == "extruder_nr":
                    extruder_stack = ExtruderManager.getInstance().getExtruderStack(int(setting_value))
                    if extruder_stack:
                        um_node.callDecoration("setActiveExtruder", extruder_stack.getId())
                    else:
                        Logger.log("w", "Unable to find extruder in position %s", setting_value)
                    continue
                if key == "print_order":
                    um_node.printOrder = int(setting_value)
                    continue
                if key =="drop_to_buildplate":
                    um_node.setSetting(SceneNodeSettings.AutoDropDown, parseBool(setting_value))
                    continue
                if key in known_setting_keys:
                    setting_container.setProperty(key, "value", setting_value)
                else:
                    um_node.metadata[key] = settings[key]

        if len(um_node.getChildren()) > 0 and um_node.getMeshData() is None:
            if len(um_node.getAllChildren()) == 1:
                # We don't want groups of one, so move the node up one "level"
                child_node = um_node.getChildren()[0]
                # Move all the meshes of children so that toolhandles are shown in the correct place.
                if child_node.getMeshData():
                    extents = child_node.getMeshData().getExtents()
                    move_matrix = Matrix()
                    move_matrix.translate(-extents.center)
                    child_node.setMeshData(child_node.getMeshData().getTransformed(move_matrix))
                    child_node.translate(extents.center)
                parent_transformation = um_node.getLocalTransformation()
                child_transformation = child_node.getLocalTransformation()
                child_node.setTransformation(parent_transformation.multiply(child_transformation))
                um_node = cast(CuraSceneNode, um_node.getChildren()[0])
            else:
                group_decorator = GroupDecorator()
                um_node.addDecorator(group_decorator)
        um_node.setSelectable(True)
        if um_node.getMeshData():
            # Assuming that all nodes with mesh data are printable objects
            # affects (auto) slicing
            sliceable_decorator = SliceableObjectDecorator()
            um_node.addDecorator(sliceable_decorator)
        return um_node

    def _read(self, file_name: str) -> Union[SceneNode, List[SceneNode]]:
        self._empty_project = False
        result = []
        # The base object of 3mf is a zipped archive.
        try:
            archive = zipfile.ZipFile(file_name, "r")
            self._base_name = os.path.basename(file_name)
            parser = Savitar.ThreeMFParser()
            scene_3mf = parser.parse(archive.open("3D/3dmodel.model").read())
            self._unit = scene_3mf.getUnit()

            for key, value in scene_3mf.getMetadata().items():
                CuraApplication.getInstance().getController().getScene().setMetaDataEntry(key, value)

            for node in scene_3mf.getSceneNodes():
                um_node = ThreeMFReader._convertSavitarNodeToUMNode(node, file_name, archive)
                if um_node is None:
                    continue

                # compensate for original center position, if object(s) is/are not around its zero position
                transform_matrix = Matrix()
                mesh_data = um_node.getMeshData()
                if mesh_data is not None:
                    extents = mesh_data.getExtents()
                    if extents is not None:
                        center_vector = Vector(extents.center.x, extents.center.y, extents.center.z)
                        transform_matrix.setByTranslation(center_vector)
                transform_matrix.multiply(um_node.getLocalTransformation())
                um_node.setTransformation(transform_matrix)

                global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()

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

                # Third step: 3MF also defines a unit, whereas Cura always assumes mm.
                scale_matrix = Matrix()
                scale_matrix.setByScaleVector(self._getScaleFromUnit(self._unit))
                transformation_matrix.multiply(scale_matrix)

                # Pre multiply the transformation with the loaded transformation, so the data is handled correctly.
                um_node.setTransformation(um_node.getLocalTransformation().preMultiply(transformation_matrix))

                # Check if the model is positioned below the build plate and honor that when loading project files.
                node_meshdata = um_node.getMeshData()
                if node_meshdata is not None:
                    aabb = node_meshdata.getExtents(um_node.getWorldTransformation())
                    if aabb is not None:
                        minimum_z_value = aabb.minimum.y  # y is z in transformation coordinates
                        if minimum_z_value < 0:
                            um_node.addDecorator(ZOffsetDecorator())
                            um_node.callDecoration("setZOffset", minimum_z_value)

                result.append(um_node)

            if len(result) == 0:
                self._empty_project = True

        except Exception:
            Logger.logException("e", "An exception occurred in 3mf reader.")
            return []

        return result

    def _getScaleFromUnit(self, unit: Optional[str]) -> Vector:
        """Create a scale vector based on a unit string.

        .. The core spec defines the following:
        * micron
        * millimeter (default)
        * centimeter
        * inch
        * foot
        * meter
        """
        conversion_to_mm = {
            "micron": 0.001,
            "millimeter": 1,
            "centimeter": 10,
            "meter": 1000,
            "inch": 25.4,
            "foot": 304.8
        }
        if unit is None:
            unit = "millimeter"
        elif unit not in conversion_to_mm:
            Logger.log("w", "Unrecognised unit {unit} used. Assuming mm instead.".format(unit=unit))
            unit = "millimeter"

        scale = conversion_to_mm[unit]
        return Vector(scale, scale, scale)

    @staticmethod
    def stringToSceneNodes(scene_string: str) -> List[SceneNode]:
        parser = Savitar.ThreeMFParser()
        scene = parser.parse(scene_string)

        # Convert the scene to scene nodes
        nodes = []
        for savitar_node in scene.getSceneNodes():
            scene_node = ThreeMFReader._convertSavitarNodeToUMNode(savitar_node, "file_name")
            if scene_node is None:
                continue
            nodes.append(scene_node)

        return nodes
