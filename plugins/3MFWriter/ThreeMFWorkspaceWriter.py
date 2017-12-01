# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Workspace.WorkspaceWriter import WorkspaceWriter
from UM.Application import Application
from UM.Preferences import Preferences
from UM.Settings.ContainerRegistry import ContainerRegistry
from cura.Settings.ExtruderManager import ExtruderManager
import zipfile
from io import StringIO
import configparser


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
        if archive is None:  # This happens if there was no mesh data to write.
            archive = zipfile.ZipFile(stream, "w", compression = zipfile.ZIP_DEFLATED)

        global_container_stack = Application.getInstance().getGlobalContainerStack()

        # Add global container stack data to the archive.
        self._writeContainerToArchive(global_container_stack, archive)

        # Also write all containers in the stack to the file
        for container in global_container_stack.getContainers():
            self._writeContainerToArchive(container, archive)

        # Check if the machine has extruders and save all that data as well.
        for extruder_stack in ExtruderManager.getInstance().getMachineExtruders(global_container_stack.getId()):
            self._writeContainerToArchive(extruder_stack, archive)
            for container in extruder_stack.getContainers():
                self._writeContainerToArchive(container, archive)

        # Write preferences to archive
        original_preferences = Preferences.getInstance() #Copy only the preferences that we use to the workspace.
        temp_preferences = Preferences()
        for preference in {"general/visible_settings", "cura/active_mode", "cura/categories_expanded"}:
            temp_preferences.addPreference(preference, None)
            temp_preferences.setValue(preference, original_preferences.getValue(preference))
        preferences_string = StringIO()
        temp_preferences.writeToFile(preferences_string)
        preferences_file = zipfile.ZipInfo("Cura/preferences.cfg")
        archive.writestr(preferences_file, preferences_string.getvalue())

        # Save Cura version
        version_file = zipfile.ZipInfo("Cura/version.ini")
        version_config_parser = configparser.ConfigParser()
        version_config_parser.add_section("versions")
        version_config_parser.set("versions", "cura_version", Application.getStaticVersion())

        version_file_string = StringIO()
        version_config_parser.write(version_file_string)
        archive.writestr(version_file, version_file_string.getvalue())

        # Close the archive & reset states.
        archive.close()
        mesh_writer.setStoreArchive(False)
        return True

    ##  Helper function that writes ContainerStacks, InstanceContainers and DefinitionContainers to the archive.
    #   \param container That follows the \type{ContainerInterface} to archive.
    #   \param archive The archive to write to.
    @staticmethod
    def _writeContainerToArchive(container, archive):
        if isinstance(container, type(ContainerRegistry.getInstance().getEmptyInstanceContainer())):
            return  # Empty file, do nothing.

        file_suffix = ContainerRegistry.getMimeTypeForContainer(type(container)).preferredSuffix

        # Some containers have a base file, which should then be the file to use.
        if "base_file" in container.getMetaData():
            base_file = container.getMetaDataEntry("base_file")
            container = ContainerRegistry.getInstance().findContainers(id = base_file)[0]

        file_name = "Cura/%s.%s" % (container.getId(), file_suffix)

        if file_name in archive.namelist():
            return  # File was already saved, no need to do it again. Uranium guarantees unique ID's, so this should hold.

        file_in_archive = zipfile.ZipInfo(file_name)
        # For some reason we have to set the compress type of each file as well (it doesn't keep the type of the entire archive)
        file_in_archive.compress_type = zipfile.ZIP_DEFLATED

        # Do not include the network authentication keys
        ignore_keys = ["network_authentication_id", "network_authentication_key"]
        serialized_data = container.serialize(ignored_metadata_keys = ignore_keys)

        archive.writestr(file_in_archive, serialized_data)
