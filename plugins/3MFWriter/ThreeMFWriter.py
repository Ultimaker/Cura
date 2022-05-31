#  Copyright (c) 2015-2022 Ultimaker B.V.
#  Cura is released under the terms of the LGPLv3 or higher.
import json

from typing import Optional, cast, List, Dict

from UM.Mesh.MeshWriter import MeshWriter
from UM.Math.Vector import Vector
from UM.Logger import Logger
from UM.Math.Matrix import Matrix
from UM.Application import Application
from UM.Scene.SceneNode import SceneNode

from cura.CuraApplication import CuraApplication
from cura.CuraPackageManager import CuraPackageManager
from cura.Utils.Threading import call_on_qt_thread
from cura.Snapshot import Snapshot

from PyQt6.QtCore import QBuffer

import pySavitar as Savitar

import numpy
import datetime

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

THUMBNAIL_PATH = "Metadata/thumbnail.png"
MODEL_PATH = "3D/3dmodel.model"
PACKAGE_METADATA_PATH = "Metadata/packages.json"

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
        self._archive: Optional[zipfile.ZipFile] = None
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
                savitar_node.setSetting("cura:" + key, str(stack.getProperty(key, "value")))

        # Store the metadata.
        for key, value in um_node.metadata.items():
            savitar_node.setSetting(key, value)

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

    def write(self, stream, nodes, mode = MeshWriter.OutputMode.BinaryMode) -> bool:
        self._archive = None # Reset archive
        archive = zipfile.ZipFile(stream, "w", compression = zipfile.ZIP_DEFLATED)
        try:
            model_file = zipfile.ZipInfo(MODEL_PATH)
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
            model_relation_element = ET.SubElement(relations_element, "Relationship", Target = "/" + MODEL_PATH, Id = "rel0", Type = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel")

            # Attempt to add a thumbnail
            snapshot = self._createSnapshot()
            if snapshot:
                thumbnail_buffer = QBuffer()
                thumbnail_buffer.open(QBuffer.OpenModeFlag.ReadWrite)
                snapshot.save(thumbnail_buffer, "PNG")

                thumbnail_file = zipfile.ZipInfo(THUMBNAIL_PATH)
                # Don't try to compress snapshot file, because the PNG is pretty much as compact as it will get
                archive.writestr(thumbnail_file, thumbnail_buffer.data())

                # Add PNG to content types file
                thumbnail_type = ET.SubElement(content_types, "Default", Extension = "png", ContentType = "image/png")
                # Add thumbnail relation to _rels/.rels file
                thumbnail_relation_element = ET.SubElement(relations_element, "Relationship", Target = "/" + THUMBNAIL_PATH, Id = "rel1", Type = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail")

            # Write material metadata
            material_metadata = self._getMaterialPackageMetadata()
            self._storeMetadataJson({"packages": material_metadata}, archive, PACKAGE_METADATA_PATH)

            savitar_scene = Savitar.Scene()

            scene_metadata = CuraApplication.getInstance().getController().getScene().getMetaData()

            for key, value in scene_metadata.items():
                savitar_scene.setMetaDataEntry(key, value)

            current_time_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if "Application" not in scene_metadata:
                # This might sound a bit strange, but this field should store the original application that created
                # the 3mf. So if it was already set, leave it to whatever it was.
                savitar_scene.setMetaDataEntry("Application", CuraApplication.getInstance().getApplicationDisplayName())
            if "CreationDate" not in scene_metadata:
                savitar_scene.setMetaDataEntry("CreationDate", current_time_string)

            savitar_scene.setMetaDataEntry("ModificationDate", current_time_string)

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

    @staticmethod
    def _storeMetadataJson(metadata: Dict[str, List[Dict[str, str]]], archive: zipfile.ZipFile, path: str) -> None:
        """Stores metadata inside archive path as json file"""
        metadata_file = zipfile.ZipInfo(path)
        # We have to set the compress type of each file as well (it doesn't keep the type of the entire archive)
        metadata_file.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(metadata_file, json.dumps(metadata, separators=(", ", ": "), indent=4, skipkeys=True, ensure_ascii=False))

    @staticmethod
    def _getMaterialPackageMetadata() -> List[Dict[str, str]]:
        """Get metadata for installed materials in active extruder stack, this does not include bundled materials.

        :return: List of material metadata dictionaries.
        """
        metadata = {}

        package_manager = cast(CuraPackageManager, CuraApplication.getInstance().getPackageManager())

        for extruder in CuraApplication.getInstance().getExtruderManager().getActiveExtruderStacks():
            if not extruder.isEnabled:
                # Don't export materials not in use
                continue

            package_id = package_manager.getMaterialFilePackageId(extruder.material.getFileName(), extruder.material.getMetaDataEntry("GUID"))
            package_data = package_manager.getInstalledPackageInfo(package_id)

            if not package_data or package_data.get("is_bundled"):
                continue

            material_metadata = {"id": package_id,
                                 "display_name": package_data.get("display_name") if package_data.get("display_name") else "",
                                 "website": package_data.get("website") if package_data.get("website") else "",
                                 "package_version": package_data.get("package_version") if package_data.get("package_version") else "",
                                 "sdk_version_semver": package_data.get("sdk_version_semver") if package_data.get("sdk_version_semver") else ""}

            metadata[package_id] = material_metadata

        # Storing in a dict and fetching values to avoid duplicates
        return list(metadata.values())

    @call_on_qt_thread  # must be called from the main thread because of OpenGL
    def _createSnapshot(self):
        Logger.log("d", "Creating thumbnail image...")
        if not CuraApplication.getInstance().isVisible:
            Logger.log("w", "Can't create snapshot when renderer not initialized.")
            return None
        try:
            snapshot = Snapshot.snapshot(width = 300, height = 300)
        except:
            Logger.logException("w", "Failed to create snapshot image")
            return None

        return snapshot
