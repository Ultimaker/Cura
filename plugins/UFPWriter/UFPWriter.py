# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import cast, List, Dict

from Charon.VirtualFile import VirtualFile  # To open UFP files.
from Charon.OpenMode import OpenMode  # To indicate that we want to write to UFP files.
from io import StringIO  # For converting g-code to bytes.

from UM.Logger import Logger
from UM.Mesh.MeshWriter import MeshWriter  # The writer we need to implement.
from UM.MimeTypeDatabase import MimeTypeDatabase, MimeType
from UM.PluginRegistry import PluginRegistry  # To get the g-code writer.
from PyQt5.QtCore import QBuffer

from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from cura.CuraApplication import CuraApplication
from cura.Snapshot import Snapshot
from cura.Utils.Threading import call_on_qt_thread

from UM.i18n import i18nCatalog

METADATA_OBJECTS_PATH = "metadata/objects"

catalog = i18nCatalog("cura")


class UFPWriter(MeshWriter):
    def __init__(self):
        super().__init__(add_to_recent_files=False)

        MimeTypeDatabase.addMimeType(
            MimeType(
                name="application/x-ufp",
                comment="Ultimaker Format Package",
                suffixes=["ufp"]
            )
        )

        self._snapshot = None

    def _createSnapshot(self, *args):
        # must be called from the main thread because of OpenGL
        Logger.log("d", "Creating thumbnail image...")
        try:
            self._snapshot = Snapshot.snapshot(width=300, height=300)
        except Exception:
            Logger.logException("w", "Failed to create snapshot image")
            self._snapshot = None  # Failing to create thumbnail should not fail creation of UFP

    # This needs to be called on the main thread (Qt thread) because the serialization of material containers can
    # trigger loading other containers. Because those loaded containers are QtObjects, they must be created on the
    # Qt thread. The File read/write operations right now are executed on separated threads because they are scheduled
    # by the Job class.
    @call_on_qt_thread
    def write(self, stream, nodes, mode=MeshWriter.OutputMode.BinaryMode):
        archive = VirtualFile()
        archive.openStream(stream, "application/x-ufp", OpenMode.WriteOnly)

        self._writeObjectList(archive)

        # Store the g-code from the scene.
        archive.addContentType(extension="gcode", mime_type="text/x-gcode")
        gcode_textio = StringIO()  # We have to convert the g-code into bytes.
        gcode_writer = cast(MeshWriter, PluginRegistry.getInstance().getPluginObject("GCodeWriter"))
        success = gcode_writer.write(gcode_textio, None)
        if not success:  # Writing the g-code failed. Then I can also not write the gzipped g-code.
            self.setInformation(gcode_writer.getInformation())
            return False
        gcode = archive.getStream("/3D/model.gcode")
        gcode.write(gcode_textio.getvalue().encode("UTF-8"))
        archive.addRelation(virtual_path="/3D/model.gcode",
                            relation_type="http://schemas.ultimaker.org/package/2018/relationships/gcode")

        self._createSnapshot()

        # Store the thumbnail.
        if self._snapshot:
            archive.addContentType(extension="png", mime_type="image/png")
            thumbnail = archive.getStream("/Metadata/thumbnail.png")

            thumbnail_buffer = QBuffer()
            thumbnail_buffer.open(QBuffer.ReadWrite)
            thumbnail_image = self._snapshot
            thumbnail_image.save(thumbnail_buffer, "PNG")

            thumbnail.write(thumbnail_buffer.data())
            archive.addRelation(virtual_path="/Metadata/thumbnail.png",
                                relation_type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail",
                                origin="/3D/model.gcode")
        else:
            Logger.log("d", "Thumbnail not created, cannot save it")

        # Store the material.
        application = CuraApplication.getInstance()
        machine_manager = application.getMachineManager()
        container_registry = application.getContainerRegistry()
        global_stack = machine_manager.activeMachine

        material_extension = "xml.fdm_material"
        material_mime_type = "application/x-ultimaker-material-profile"

        try:
            archive.addContentType(extension=material_extension, mime_type=material_mime_type)
        except:
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
            material_root_query = container_registry.findContainers(id=material_root_id)
            if not material_root_query:
                Logger.log("e",
                           "Cannot find material container with root id {root_id}".format(root_id=material_root_id))
                return False
            material_container = material_root_query[0]

            try:
                serialized_material = material_container.serialize()
            except NotImplementedError:
                Logger.log("e", "Unable serialize material container with root id: %s", material_root_id)
                return False

            material_file = archive.getStream(material_file_name)
            material_file.write(serialized_material.encode("UTF-8"))
            archive.addRelation(virtual_path=material_file_name,
                                relation_type="http://schemas.ultimaker.org/package/2018/relationships/material",
                                origin="/3D/model.gcode")

            added_materials.append(material_file_name)

        try:
            archive.close()
        except OSError as e:
            error_msg = catalog.i18nc("@info:error", "Can't write to UFP file:") + " " + str(e)
            self.setInformation(error_msg)
            Logger.error(error_msg)
            return False
        return True

    @staticmethod
    def _writeObjectList(archive):
        """Write a json list of object names to the METADATA_OBJECTS_PATH metadata field

        To retrieve, use: `archive.getMetadata(METADATA_OBJECTS_PATH)`
        """

        objects_model = CuraApplication.getInstance().getObjectsModel()
        object_metas = []

        for item in objects_model.items:
            object_metas.extend(UFPWriter._getObjectMetas(item["node"]))

        data = {METADATA_OBJECTS_PATH: object_metas}
        archive.setMetadata(data)

    @staticmethod
    def _getObjectMetas(node: SceneNode) -> List[Dict[str, str]]:
        """Get object metadata to write for a Node.

        :return: List of object metadata dictionaries.
                 Might contain > 1 element in case of a group node.
                 Might be empty in case of nonPrintingMesh
        """

        return [{"name": item.getName()}
                for item in DepthFirstIterator(node)
                if item.getMeshData() is not None and not item.callDecoration("isNonPrintingMesh")
                ]
