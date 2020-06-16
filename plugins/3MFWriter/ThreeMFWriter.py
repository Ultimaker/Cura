# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.
from typing import Optional

from UM.Mesh.MeshWriter import MeshWriter
from UM.Math.Vector import Vector
from UM.Logger import Logger
from UM.Math.Matrix import Matrix
from UM.Application import Application
from UM.Scene.SceneNode import SceneNode

from cura.CuraApplication import CuraApplication

import Savitar

import numpy

MYPY = False
try:
    if not MYPY:
        import xml.etree.cElementTree as ET
except ImportError:
    Logger.log("w", "Unable to load cElementTree, switching to slower version")
    import xml.etree.ElementTree as ET

import zipfile
import UM.Application

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


class ThreeMFWriter(MeshWriter):
    def __init__(self):
        super().__init__()
        self._namespaces = {
            "3mf": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02",
            "content-types": "http://schemas.openxmlformats.org/package/2006/content-types",
            "relationships": "http://schemas.openxmlformats.org/package/2006/relationships",
            "cura": "http://software.ultimaker.com/xml/cura/3mf/2015/10"
        }

        self._unit_matrix_string = self._convertMatrixToString(Matrix())
        self._archive = None  # type: Optional[zipfile.ZipFile]
        self._store_archive = False

    def _convertMatrixToString(self, matrix):
        result = ""
        result += str(matrix._data[0, 0]) + " "
        result += str(matrix._data[1, 0]) + " "
        result += str(matrix._data[2, 0]) + " "
        result += str(matrix._data[0, 1]) + " "
        result += str(matrix._data[1, 1]) + " "
        result += str(matrix._data[2, 1]) + " "
        result += str(matrix._data[0, 2]) + " "
        result += str(matrix._data[1, 2]) + " "
        result += str(matrix._data[2, 2]) + " "
        result += str(matrix._data[0, 3]) + " "
        result += str(matrix._data[1, 3]) + " "
        result += str(matrix._data[2, 3])
        return result

    def setStoreArchive(self, store_archive):
        """Should we store the archive

        Note that if this is true, the archive will not be closed.
        The object that set this parameter is then responsible for closing it correctly!
        """
        self._store_archive = store_archive

    def _convertUMNodeToSavitarNode(self, um_node, transformation = Matrix()):
        """Convenience function that converts an Uranium SceneNode object to a SavitarSceneNode

        :returns: Uranium Scene node.
        """
        if not isinstance(um_node, SceneNode):
            return None

        active_build_plate_nr = CuraApplication.getInstance().getMultiBuildPlateModel().activeBuildPlate
        if um_node.callDecoration("getBuildPlateNumber") != active_build_plate_nr:
            return

        savitar_node = Savitar.SceneNode()
        savitar_node.setName(um_node.getName())

        node_matrix = um_node.getLocalTransformation()

        matrix_string = self._convertMatrixToString(node_matrix.preMultiply(transformation))

        savitar_node.setTransformation(matrix_string)
        mesh_data = um_node.getMeshData()
        if mesh_data is not None:
            savitar_node.getMeshData().setVerticesFromBytes(mesh_data.getVerticesAsByteArray())
            indices_array = mesh_data.getIndicesAsByteArray()
            if indices_array is not None:
                savitar_node.getMeshData().setFacesFromBytes(indices_array)
            else:
                savitar_node.getMeshData().setFacesFromBytes(numpy.arange(mesh_data.getVertices().size / 3, dtype=numpy.int32).tostring())

        # Handle per object settings (if any)
        stack = um_node.callDecoration("getStack")
        if stack is not None:
            changed_setting_keys = stack.getTop().getAllKeys()

            # Ensure that we save the extruder used for this object in a multi-extrusion setup
            if stack.getProperty("machine_extruder_count", "value") > 1:
                changed_setting_keys.add("extruder_nr")

            # Get values for all changed settings & save them.
            for key in changed_setting_keys:
                savitar_node.setSetting(key, str(stack.getProperty(key, "value")))

        for child_node in um_node.getChildren():
            # only save the nodes on the active build plate
            if child_node.callDecoration("getBuildPlateNumber") != active_build_plate_nr:
                continue
            savitar_child_node = self._convertUMNodeToSavitarNode(child_node)
            if savitar_child_node is not None:
                savitar_node.addChild(savitar_child_node)

        return savitar_node

    def getArchive(self):
        return self._archive

    def write(self, stream, nodes, mode = MeshWriter.OutputMode.BinaryMode):
        self._archive = None # Reset archive
        archive = zipfile.ZipFile(stream, "w", compression = zipfile.ZIP_DEFLATED)
        try:
            model_file = zipfile.ZipInfo("3D/3dmodel.model")
            # Because zipfile is stupid and ignores archive-level compression settings when writing with ZipInfo.
            model_file.compress_type = zipfile.ZIP_DEFLATED

            # Create content types file
            content_types_file = zipfile.ZipInfo("[Content_Types].xml")
            content_types_file.compress_type = zipfile.ZIP_DEFLATED
            content_types = ET.Element("Types", xmlns = self._namespaces["content-types"])
            rels_type = ET.SubElement(content_types, "Default", Extension = "rels", ContentType = "application/vnd.openxmlformats-package.relationships+xml")
            model_type = ET.SubElement(content_types, "Default", Extension = "model", ContentType = "application/vnd.ms-package.3dmanufacturing-3dmodel+xml")

            # Create _rels/.rels file
            relations_file = zipfile.ZipInfo("_rels/.rels")
            relations_file.compress_type = zipfile.ZIP_DEFLATED
            relations_element = ET.Element("Relationships", xmlns = self._namespaces["relationships"])
            model_relation_element = ET.SubElement(relations_element, "Relationship", Target = "/3D/3dmodel.model", Id = "rel0", Type = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel")

            savitar_scene = Savitar.Scene()
            transformation_matrix = Matrix()
            transformation_matrix._data[1, 1] = 0
            transformation_matrix._data[1, 2] = -1
            transformation_matrix._data[2, 1] = 1
            transformation_matrix._data[2, 2] = 0

            global_container_stack = Application.getInstance().getGlobalContainerStack()
            # Second step: 3MF defines the left corner of the machine as center, whereas cura uses the center of the
            # build volume.
            if global_container_stack:
                translation_vector = Vector(x=global_container_stack.getProperty("machine_width", "value") / 2,
                                            y=global_container_stack.getProperty("machine_depth", "value") / 2,
                                            z=0)
                translation_matrix = Matrix()
                translation_matrix.setByTranslation(translation_vector)
                transformation_matrix.preMultiply(translation_matrix)

            root_node = UM.Application.Application.getInstance().getController().getScene().getRoot()
            for node in nodes:
                if node == root_node:
                    for root_child in node.getChildren():
                        savitar_node = self._convertUMNodeToSavitarNode(root_child, transformation_matrix)
                        if savitar_node:
                            savitar_scene.addSceneNode(savitar_node)
                else:
                    savitar_node = self._convertUMNodeToSavitarNode(node, transformation_matrix)
                    if savitar_node:
                        savitar_scene.addSceneNode(savitar_node)

            parser = Savitar.ThreeMFParser()
            scene_string = parser.sceneToString(savitar_scene)

            archive.writestr(model_file, scene_string)
            archive.writestr(content_types_file, b'<?xml version="1.0" encoding="UTF-8"?> \n' + ET.tostring(content_types))
            archive.writestr(relations_file, b'<?xml version="1.0" encoding="UTF-8"?> \n' + ET.tostring(relations_element))
        except Exception as e:
            Logger.logException("e", "Error writing zip file")
            self.setInformation(catalog.i18nc("@error:zip", "Error writing 3mf file."))
            return False
        finally:
            if not self._store_archive:
                archive.close()
            else:
                self._archive = archive

        return True
