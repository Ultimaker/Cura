#Copyright (c) 2019 Ultimaker B.V.
#Cura is released under the terms of the LGPLv3 or higher.

from typing import cast

from Charon.VirtualFile import VirtualFile #To open UFP files.
from Charon.OpenMode import OpenMode #To indicate that we want to write to UFP files.
from io import StringIO #For converting g-code to bytes.

from UM.Logger import Logger
from UM.Mesh.MeshWriter import MeshWriter #The writer we need to implement.
from UM.MimeTypeDatabase import MimeTypeDatabase, MimeType
from UM.PluginRegistry import PluginRegistry #To get the g-code writer.
from PyQt5.QtCore import QBuffer

from cura.CuraApplication import CuraApplication
from cura.Snapshot import Snapshot
from cura.Utils.Threading import call_on_qt_thread

from UM.i18n import i18nCatalog
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

        self._snapshot = None

    def _createSnapshot(self, *args):
        # must be called from the main thread because of OpenGL
        Logger.log("d", "Creating thumbnail image...")
        self._snapshot = Snapshot.snapshot(width = 300, height = 300)

    # This needs to be called on the main thread (Qt thread) because the serialization of material containers can
    # trigger loading other containers. Because those loaded containers are QtObjects, they must be created on the
    # Qt thread. The File read/write operations right now are executed on separated threads because they are scheduled
    # by the Job class.
    @call_on_qt_thread
    def write(self, stream, nodes, mode = MeshWriter.OutputMode.BinaryMode):
        archive = VirtualFile()
        archive.openStream(stream, "application/x-ufp", OpenMode.WriteOnly)

        #Store the g-code from the scene.
        archive.addContentType(extension = "gcode", mime_type = "text/x-gcode")
        gcode_textio = StringIO() #We have to convert the g-code into bytes.
        gcode_writer = cast(MeshWriter, PluginRegistry.getInstance().getPluginObject("GCodeWriter"))
        success = gcode_writer.write(gcode_textio, None)
        if not success: #Writing the g-code failed. Then I can also not write the gzipped g-code.
            self.setInformation(gcode_writer.getInformation())
            return False
        gcode = archive.getStream("/3D/model.gcode")
        gcode.write(gcode_textio.getvalue().encode("UTF-8"))
        archive.addRelation(virtual_path = "/3D/model.gcode", relation_type = "http://schemas.ultimaker.org/package/2018/relationships/gcode")

        self._createSnapshot()

        #Store the thumbnail.
        if self._snapshot:
            archive.addContentType(extension = "png", mime_type = "image/png")
            thumbnail = archive.getStream("/Metadata/thumbnail.png")

            thumbnail_buffer = QBuffer()
            thumbnail_buffer.open(QBuffer.ReadWrite)
            thumbnail_image = self._snapshot
            thumbnail_image.save(thumbnail_buffer, "PNG")

            thumbnail.write(thumbnail_buffer.data())
            archive.addRelation(virtual_path = "/Metadata/thumbnail.png", relation_type = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail", origin = "/3D/model.gcode")
        else:
            Logger.log("d", "Thumbnail not created, cannot save it")

        # Store the material.
        application = CuraApplication.getInstance()
        machine_manager = application.getMachineManager()
        material_manager = application.getMaterialManager()
        global_stack = machine_manager.activeMachine

        material_extension = "xml.fdm_material"
        material_mime_type = "application/x-ultimaker-material-profile"

        try:
            archive.addContentType(extension = material_extension, mime_type = material_mime_type)
        except:
            Logger.log("w", "The material extension: %s was already added", material_extension)

        added_materials = []
        for extruder_stack in global_stack.extruders.values():
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
            material_group = material_manager.getMaterialGroup(material_root_id)
            if material_group is None:
                Logger.log("e", "Cannot find material container with root id [%s]", material_root_id)
                return False

            material_container = material_group.root_material_node.container
            try:
                serialized_material = material_container.serialize()
            except NotImplementedError:
                Logger.log("e", "Unable serialize material container with root id: %s", material_root_id)
                return False

            material_file = archive.getStream(material_file_name)
            material_file.write(serialized_material.encode("UTF-8"))
            archive.addRelation(virtual_path = material_file_name,
                                relation_type = "http://schemas.ultimaker.org/package/2018/relationships/material",
                                origin = "/3D/model.gcode")

            added_materials.append(material_file_name)

        archive.close()
        return True
