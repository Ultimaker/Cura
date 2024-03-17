#  Copyright (c) 2015-2022 Ultimaker B.V.
#  Cura is released under the terms of the LGPLv3 or higher.
import json
import re
import threading

from typing import Optional, cast, List, Dict, Pattern, Set

from UM.Mesh.MeshWriter import MeshWriter
from UM.Math.Vector import Vector
from UM.Logger import Logger
from UM.Math.Matrix import Matrix
from UM.Application import Application
from UM.OutputDevice import OutputDeviceError
from UM.Message import Message
from UM.Resources import Resources
from UM.Scene.SceneNode import SceneNode
from UM.Settings.ContainerRegistry import ContainerRegistry

from cura.CuraApplication import CuraApplication
from cura.CuraPackageManager import CuraPackageManager
from cura.Settings import CuraContainerStack
from cura.Utils.Threading import call_on_qt_thread
from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.Snapshot import Snapshot

from PyQt6.QtCore import Qt, QBuffer
from PyQt6.QtGui import QImage, QPainter

import pySavitar as Savitar
from .UCPDialog import UCPDialog
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

from .SettingsExportModel import SettingsExportModel
from .SettingsExportGroup import SettingsExportGroup

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

THUMBNAIL_PATH = "Metadata/thumbnail.png"
MODEL_PATH = "3D/3dmodel.model"
PACKAGE_METADATA_PATH = "Cura/packages.json"

class ThreeMFWriter(MeshWriter):
    def __init__(self):
        super().__init__()
        self._namespaces = {
            "3mf": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02",
            "content-types": "http://schemas.openxmlformats.org/package/2006/content-types",
            "relationships": "http://schemas.openxmlformats.org/package/2006/relationships",
            "cura": "http://software.ultimaker.com/xml/cura/3mf/2015/10"
        }

        self._unit_matrix_string = ThreeMFWriter._convertMatrixToString(Matrix())
        self._archive: Optional[zipfile.ZipFile] = None
        self._store_archive = False
        self._lock = threading.Lock()

    @staticmethod
    def _convertMatrixToString(matrix):
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

    @staticmethod
    def _convertUMNodeToSavitarNode(um_node,
                                    transformation = Matrix(),
                                    exported_settings: Optional[Dict[str, Set[str]]] = None):
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

        node_matrix = Matrix()
        mesh_data = um_node.getMeshData()
        # compensate for original center position, if object(s) is/are not around its zero position
        if mesh_data is not None:
            extents = mesh_data.getExtents()
            if extents is not None:
                # We use a different coordinate space while writing, so flip Z and Y
                center_vector = Vector(extents.center.x, extents.center.z, extents.center.y)
                node_matrix.setByTranslation(center_vector)
        node_matrix.multiply(um_node.getLocalTransformation())

        matrix_string = ThreeMFWriter._convertMatrixToString(node_matrix.preMultiply(transformation))

        savitar_node.setTransformation(matrix_string)
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

            if exported_settings is None:
                # Ensure that we save the extruder used for this object in a multi-extrusion setup
                if stack.getProperty("machine_extruder_count", "value") > 1:
                    changed_setting_keys.add("extruder_nr")

                # Get values for all changed settings & save them.
                for key in changed_setting_keys:
                    savitar_node.setSetting("cura:" + key, str(stack.getProperty(key, "value")))
            else:
                 # We want to export only the specified settings
                if um_node.getName() in exported_settings:
                    model_exported_settings = exported_settings[um_node.getName()]

                    # Get values for all exported settings & save them.
                    for key in model_exported_settings:
                        savitar_node.setSetting("cura:" + key, str(stack.getProperty(key, "value")))

        if isinstance(um_node, CuraSceneNode):
            savitar_node.setSetting("cura:print_order", str(um_node.printOrder))
            savitar_node.setSetting("cura:drop_to_buildplate", str(um_node.isDropDownEnabled))

        # Store the metadata.
        for key, value in um_node.metadata.items():
            savitar_node.setSetting(key, value)

        for child_node in um_node.getChildren():
            # only save the nodes on the active build plate
            if child_node.callDecoration("getBuildPlateNumber") != active_build_plate_nr:
                continue
            savitar_child_node = ThreeMFWriter._convertUMNodeToSavitarNode(child_node,
                                                                           exported_settings = exported_settings)
            if savitar_child_node is not None:
                savitar_node.addChild(savitar_child_node)

        return savitar_node

    def getArchive(self):
        return self._archive

    def _addLogoToThumbnail(self, primary_image, logo_name):
        # Load the icon png image
        icon_image = QImage(Resources.getPath(Resources.Images,  logo_name))

        # Resize icon_image to be 1/4 of primary_image size
        new_width = int(primary_image.width() / 4)
        new_height = int(primary_image.height() / 4)
        icon_image = icon_image.scaled(new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio)
        # Create a QPainter to draw on the image
        painter = QPainter(primary_image)

        # Draw the icon in the top-left corner (adjust coordinates as needed)
        icon_position = (10, 10)
        painter.drawImage(icon_position[0], icon_position[1], icon_image)

        painter.end()

    def write(self, stream, nodes, mode = MeshWriter.OutputMode.BinaryMode, export_settings_model = None) -> bool:
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
                if export_settings_model != None:
                    self._addLogoToThumbnail(snapshot, "cura-share.png")
                elif export_settings_model == None and self._store_archive:
                    self._addLogoToThumbnail(snapshot, "cura-icon.png")
                thumbnail_buffer = QBuffer()
                thumbnail_buffer.open(QBuffer.OpenModeFlag.ReadWrite)
                snapshot.save(thumbnail_buffer, "PNG")

                thumbnail_file = zipfile.ZipInfo(THUMBNAIL_PATH)
                # Don't try to compress snapshot file, because the PNG is pretty much as compact as it will get
                archive.writestr(thumbnail_file, thumbnail_buffer.data())

                # Add PNG to content types file
                thumbnail_type = ET.SubElement(content_types, "Default", Extension="png", ContentType="image/png")
                # Add thumbnail relation to _rels/.rels file
                thumbnail_relation_element = ET.SubElement(relations_element, "Relationship",
                                                           Target="/" + THUMBNAIL_PATH, Id="rel1",
                                                           Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail")

            # Write material metadata
            packages_metadata = self._getMaterialPackageMetadata() + self._getPluginPackageMetadata()
            self._storeMetadataJson({"packages": packages_metadata}, archive, PACKAGE_METADATA_PATH)

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
            exported_model_settings = ThreeMFWriter._extractModelExportedSettings(export_settings_model) if export_settings_model != None else None

            for node in nodes:
                if node == root_node:
                    for root_child in node.getChildren():
                        savitar_node = ThreeMFWriter._convertUMNodeToSavitarNode(root_child,
                                                                                 transformation_matrix,
                                                                                 exported_model_settings)
                        if savitar_node:
                            savitar_scene.addSceneNode(savitar_node)
                else:
                    savitar_node = self._convertUMNodeToSavitarNode(node,
                                                                    transformation_matrix,
                                                                    exported_model_settings)
                    if savitar_node:
                        savitar_scene.addSceneNode(savitar_node)

            parser = Savitar.ThreeMFParser()
            scene_string = parser.sceneToString(savitar_scene)

            archive.writestr(model_file, scene_string)
            archive.writestr(content_types_file, b'<?xml version="1.0" encoding="UTF-8"?> \n' + ET.tostring(content_types))
            archive.writestr(relations_file, b'<?xml version="1.0" encoding="UTF-8"?> \n' + ET.tostring(relations_element))
        except Exception as error:
            Logger.logException("e", "Error writing zip file")
            self.setInformation(str(error))
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
        archive.writestr(metadata_file,
                         json.dumps(metadata, separators=(", ", ": "), indent=4, skipkeys=True, ensure_ascii=False))

    @staticmethod
    def _getPluginPackageMetadata() -> List[Dict[str, str]]:
        """Get metadata for all backend plugins that are used in the project.

        :return: List of material metadata dictionaries.
        """

        backend_plugin_enum_value_regex = re.compile(
            r"PLUGIN::(?P<plugin_id>\w+)@(?P<version>\d+.\d+.\d+)::(?P<value>\w+)")
        # This regex parses enum values to find if they contain custom
        # backend engine values. These custom enum values are in the format
        #      PLUGIN::<plugin_id>@<version>::<value>
        # where
        #  - plugin_id is the id of the plugin
        #  - version is in the semver format
        #  - value is the value of the enum

        plugin_ids = set()

        def addPluginIdsInStack(stack: CuraContainerStack) -> None:
            for key in stack.getAllKeys():
                value = str(stack.getProperty(key, "value"))
                for plugin_id, _version, _value in backend_plugin_enum_value_regex.findall(value):
                    plugin_ids.add(plugin_id)

        # Go through all stacks and find all the plugin id contained in the project
        global_stack = CuraApplication.getInstance().getMachineManager().activeMachine
        addPluginIdsInStack(global_stack)

        for container in global_stack.getContainers():
            addPluginIdsInStack(container)

        for extruder_stack in global_stack.extruderList:
            addPluginIdsInStack(extruder_stack)

            for container in extruder_stack.getContainers():
                addPluginIdsInStack(container)

        metadata = {}

        package_manager = cast(CuraPackageManager, CuraApplication.getInstance().getPackageManager())
        for plugin_id in plugin_ids:
            package_data = package_manager.getInstalledPackageInfo(plugin_id)

            metadata[plugin_id] = {
                "id": plugin_id,
                "display_name": package_data.get("display_name") if package_data.get("display_name") else "",
                "package_version": package_data.get("package_version") if package_data.get("package_version") else "",
                "sdk_version_semver": package_data.get("sdk_version_semver") if package_data.get(
                    "sdk_version_semver") else "",
                "type": "plugin",
            }

        # Storing in a dict and fetching values to avoid duplicates
        return list(metadata.values())

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

            if isinstance(extruder.material, type(ContainerRegistry.getInstance().getEmptyInstanceContainer())):
                # This is an empty material container, no material to export
                continue

            if package_manager.isMaterialBundled(extruder.material.getFileName(), extruder.material.getMetaDataEntry("GUID")):
                # Don't export bundled materials
                continue

            package_id = package_manager.getMaterialFilePackageId(extruder.material.getFileName(),
                                                                  extruder.material.getMetaDataEntry("GUID"))
            package_data = package_manager.getInstalledPackageInfo(package_id)

            # We failed to find the package for this material
            if not package_data:
                Logger.info(f"Could not find package for material in extruder {extruder.id}, skipping.")
                continue

            material_metadata = {
                "id": package_id,
                "display_name": package_data.get("display_name") if package_data.get("display_name") else "",
                "package_version": package_data.get("package_version") if package_data.get("package_version") else "",
                "sdk_version_semver": package_data.get("sdk_version_semver") if package_data.get(
                    "sdk_version_semver") else "",
                "type": "material",
            }

            metadata[package_id] = material_metadata

        # Storing in a dict and fetching values to avoid duplicates
        return list(metadata.values())

    @call_on_qt_thread  # must be called from the main thread because of OpenGL
    def _createSnapshot(self):
        Logger.log("d", "Creating thumbnail image...")
        self._lock.acquire()
        if not CuraApplication.getInstance().isVisible:
            Logger.log("w", "Can't create snapshot when renderer not initialized.")
            return None
        try:
            snapshot = Snapshot.snapshot(width=300, height=300)
        except:
            Logger.logException("w", "Failed to create snapshot image")
            return None
        finally: self._lock.release()

        return snapshot

    @staticmethod
    def sceneNodesToString(scene_nodes: [SceneNode]) -> str:
        savitar_scene = Savitar.Scene()
        for scene_node in scene_nodes:
            savitar_node = ThreeMFWriter._convertUMNodeToSavitarNode(scene_node)
            savitar_scene.addSceneNode(savitar_node)
        parser = Savitar.ThreeMFParser()
        scene_string = parser.sceneToString(savitar_scene)
        return scene_string

    @staticmethod
    def _extractModelExportedSettings(model: Optional[SettingsExportModel]) -> Dict[str, Set[str]]:
        extra_settings = {}

        if model is not None:
            for group in model.settingsGroups:
                if group.category == SettingsExportGroup.Category.Model:
                    exported_model_settings = set()

                    for exported_setting in group.settings:
                        if exported_setting.selected:
                            exported_model_settings.add(exported_setting.id)

                    extra_settings[group.category_details] = exported_model_settings

        return extra_settings

    def exportUcp(self):
        self._config_dialog = UCPDialog()
        self._config_dialog.show()
