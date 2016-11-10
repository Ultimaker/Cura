from UM.Workspace.WorkspaceWriter import WorkspaceWriter
from UM.Application import Application
from UM.Preferences import Preferences
import zipfile
from io import StringIO


class ThreeMFWorkspaceWriter(WorkspaceWriter):
    def __init__(self):
        super().__init__()

    def write(self, stream, nodes, mode=WorkspaceWriter.OutputMode.BinaryMode):
        mesh_writer = Application.getInstance().getMeshFileHandler().getWriter("3MFWriter")

        if not mesh_writer:  # We need to have the 3mf mesh writer, otherwise we can't save the entire workspace
            return False

        # Indicate that the 3mf mesh writer should not close the archive just yet (we still need to add stuff to it).
        mesh_writer.setStoreArchive(True)
        mesh_writer.write(stream, nodes, mode)
        archive = mesh_writer.getArchive()

        # Add global container stack data to the archive.
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        global_stack_file = zipfile.ZipInfo("Cura/%s.stack.cfg" % global_container_stack.getId())
        global_stack_file.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(global_stack_file, global_container_stack.serialize())

        # Write user changes to the archive.
        global_user_instance_container = global_container_stack.getTop()
        global_user_instance_file = zipfile.ZipInfo("Cura/%s.inst.cfg" % global_user_instance_container.getId())
        global_user_instance_container.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(global_user_instance_file, global_user_instance_container.serialize())

        # Write quality changes to the archive.
        global_quality_changes = global_container_stack.findContainer({"type": "quality_changes"})
        global_quality_changes_file = zipfile.ZipInfo("Cura/%s.inst.cfg" % global_quality_changes.getId())
        global_quality_changes.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(global_quality_changes_file, global_quality_changes.serialize())

        # Write preferences to archive
        preferences_file = zipfile.ZipInfo("Cura/preferences.cfg")
        preferences_string = StringIO()
        Preferences.getInstance().writeToFile(preferences_string)
        archive.writestr(preferences_file, preferences_string.getvalue())
        # Close the archive & reset states.
        archive.close()
        mesh_writer.setStoreArchive(False)
        return True
