# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import cast, List, Dict

from Charon.VirtualFile import VirtualFile  # To open UFP files.
from Charon.OpenMode import OpenMode  # To indicate that we want to write to UFP files.
from Charon.filetypes.OpenPackagingConvention import OPCError
from io import StringIO  # For converting g-code to bytes.

from PyQt6.QtCore import QBuffer

from UM.Logger import Logger
from UM.Mesh.MeshWriter import MeshWriter  # The writer we need to implement.
from UM.MimeTypeDatabase import MimeTypeDatabase, MimeType
from UM.PluginRegistry import PluginRegistry  # To get the g-code writer.

from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from cura.CuraApplication import CuraApplication
from cura.CuraPackageManager import CuraPackageManager
from cura.Utils.Threading import call_on_qt_thread

from UM.i18n import i18nCatalog

METADATA_OBJECTS_PATH = "metadata/objects"
METADATA_MATERIALS_PATH = "metadata/packages"

catalog = i18nCatalog("cura")


class UFPWriter(MeshWriter):
    def __init__(self):
        super().__init__(add_to_recent_files = False)

        MimeTypeDatabase.addMimeType(
            MimeType(
                name = "application/x-ufp",
                comment = "Ultimaker Format Package",
                suffixes = ["ufp"]
            )
        )

    # This needs to be called on the main thread (Qt thread) because the serialization of material containers can
    # trigger loading other containers. Because those loaded containers are QtObjects, they must be created on the
    # Qt thread. The File read/write operations right now are executed on separated threads because they are scheduled
    # by the Job class.
    @call_on_qt_thread
    def write(self, stream, nodes, mode = MeshWriter.OutputMode.BinaryMode):
        archive = VirtualFile()
        archive.openStream(stream, "application/x-ufp", OpenMode.WriteOnly)

        try:
            self._writeMetadata(archive)

            # Store the g-code from the scene.
            archive.addContentType(extension = "gcode", mime_type = "text/x-gcode")
        except EnvironmentError as e:
            error_msg = catalog.i18nc("@info:error", "Can't write to UFP file:") + " " + str(e)
            self.setInformation(error_msg)
            Logger.error(error_msg)
            return False
        gcode_textio = StringIO()  # We have to convert the g-code into bytes.
        gcode_writer = cast(MeshWriter, PluginRegistry.getInstance().getPluginObject("GCodeWriter"))
        success = gcode_writer.write(gcode_textio, None)
        if not success:  # Writing the g-code failed. Then I can also not write the gzipped g-code.
            self.setInformation(gcode_writer.getInformation())
            return False
        try:
            gcode = archive.getStream("/3D/model.gcode")
            gcode.write(gcode_textio.getvalue().encode("UTF-8"))
            archive.addRelation(virtual_path = "/3D/model.gcode", relation_type = "http://schemas.ultimaker.org/package/2018/relationships/gcode")
        except EnvironmentError as e:
            error_msg = catalog.i18nc("@info:error", "Can't write to UFP file:") + " " + str(e)
            self.setInformation(error_msg)
            Logger.error(error_msg)
            return False

        # Attempt to store the thumbnail, if any:
        backend = CuraApplication.getInstance().getBackend()
        snapshot = None if getattr(backend, "getLatestSnapshot", None) is None else backend.getLatestSnapshot()
        if snapshot:
            try:
                archive.addContentType(extension = "png", mime_type = "image/png")
                thumbnail = archive.getStream("/Metadata/thumbnail.png")

                thumbnail_buffer = QBuffer()
                thumbnail_buffer.open(QBuffer.OpenModeFlag.ReadWrite)
                snapshot.save(thumbnail_buffer, "PNG")

                thumbnail.write(thumbnail_buffer.data())
                archive.addRelation(virtual_path = "/Metadata/thumbnail.png",
                                    relation_type = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail",
                                    origin = "/3D/model.gcode")
            except EnvironmentError as e:
                error_msg = catalog.i18nc("@info:error", "Can't write to UFP file:") + " " + str(e)
                self.setInformation(error_msg)
                Logger.error(error_msg)
                return False
        else:
            Logger.log("w", "Thumbnail not created, cannot save it")

        # Store the material.
        application = CuraApplication.getInstance()
        machine_manager = application.getMachineManager()
        container_registry = application.getContainerRegistry()
        global_stack = machine_manager.activeMachine

        material_extension = "xml.fdm_material"
        material_mime_type = "application/x-ultimaker-material-profile"

        try:
            archive.addContentType(extension = material_extension, mime_type = material_mime_type)
        except OPCError:
            Logger.log("w", "The material extension: %s was already added", material_extension)

        added_materials = []
        for extruder_stack in global_stack.extruderList:
            material = extruder_stack.material
            try:
                material_file_name = material.getMetaData()["base_file"] + ".xml.fdm_material"
            except KeyError:
                Logger.log("w", "Unable to get base_file for the material %s", material.getId())
                continue
            material_file_name = "/Materials/" + material_file_name

            # The same material should not be added again.
            if material_file_name in added_materials:
                continue

            material_root_id = material.getMetaDataEntry("base_file")
            material_root_query = container_registry.findContainers(id = material_root_id)
            if not material_root_query:
                Logger.log("e", "Cannot find material container with root id {root_id}".format(root_id = material_root_id))
                return False
            material_container = material_root_query[0]

            try:
                serialized_material = material_container.serialize()
            except NotImplementedError:
                Logger.log("e", "Unable serialize material container with root id: %s", material_root_id)
                return False

            try:
                material_file = archive.getStream(material_file_name)
                material_file.write(serialized_material.encode("UTF-8"))
                archive.addRelation(virtual_path = material_file_name,
                                    relation_type = "http://schemas.ultimaker.org/package/2018/relationships/material",
                                    origin = "/3D/model.gcode")
            except EnvironmentError as e:
                error_msg = catalog.i18nc("@info:error", "Can't write to UFP file:") + " " + str(e)
                self.setInformation(error_msg)
                Logger.error(error_msg)
                return False

            added_materials.append(material_file_name)

        try:
            archive.close()
        except EnvironmentError as e:
            error_msg = catalog.i18nc("@info:error", "Can't write to UFP file:") + " " + str(e)
            self.setInformation(error_msg)
            Logger.error(error_msg)
            return False
        return True

    @staticmethod
    def _writeMetadata(archive: VirtualFile):
        material_metadata = UFPWriter._getMaterialPackageMetadata()
        object_metadata = UFPWriter._getObjectMetadata()

        data = {METADATA_MATERIALS_PATH: material_metadata,
                METADATA_OBJECTS_PATH: object_metadata}

        archive.setMetadata(data)

    @staticmethod
    def _getObjectMetadata() -> List[Dict[str, str]]:
        """Get object metadata to write for a Node.

        :return: List of object metadata dictionaries.
        """
        metadata = []

        objects_model = CuraApplication.getInstance().getObjectsModel()

        for item in objects_model.items:
            for node in DepthFirstIterator(item["node"]):
                if node.getMeshData() is not None and not node.callDecoration("isNonPrintingMesh"):
                    metadata.extend({"name": node.getName()})

        return metadata

    @staticmethod
    def _getMaterialPackageMetadata() -> List[Dict[str, str]]:
        """Get metadata for installed materials in active extruder stack, this does not include bundled materials.

        :return: List of material metadata dictionaries.
        """
        metadata = []

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
                                 "display_name": package_data.get("display_name"),
                                 "website": package_data.get("website"),
                                 "package_version": package_data.get("package_version"),
                                 "sdk_version_semver": package_data.get("package_version_semver")}

            metadata.append(material_metadata)

        return metadata

