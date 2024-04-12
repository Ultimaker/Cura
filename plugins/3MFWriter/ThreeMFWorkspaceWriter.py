# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional

import configparser
from io import StringIO
from threading import Lock
import zipfile
from typing import Dict, Any

from UM.Application import Application
from UM.Logger import Logger
from UM.Preferences import Preferences
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Workspace.WorkspaceWriter import WorkspaceWriter
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

from .ThreeMFWriter import ThreeMFWriter
from .SettingsExportModel import SettingsExportModel
from .SettingsExportGroup import SettingsExportGroup

USER_SETTINGS_PATH = "Cura/user-settings.json"


class ThreeMFWorkspaceWriter(WorkspaceWriter):
    def __init__(self):
        super().__init__()
        self._ucp_model: Optional[SettingsExportModel] = None

    def setExportModel(self, model: SettingsExportModel) -> None:
        if self._ucp_model != model:
            self._ucp_model = model

    def _write(self, stream, nodes, mode=WorkspaceWriter.OutputMode.BinaryMode):
        application = Application.getInstance()
        machine_manager = application.getMachineManager()

        mesh_writer = application.getMeshFileHandler().getWriter("3MFWriter")

        if not mesh_writer:  # We need to have the 3mf mesh writer, otherwise we can't save the entire workspace
            self.setInformation(catalog.i18nc("@error:zip", "3MF Writer plug-in is corrupt."))
            Logger.error("3MF Writer class is unavailable. Can't write workspace.")
            return False

        global_stack = machine_manager.activeMachine
        if global_stack is None:
            self.setInformation(
                catalog.i18nc("@error", "There is no workspace yet to write. Please add a printer first."))
            Logger.error("Tried to write a 3MF workspace before there was a global stack.")
            return False

        # Indicate that the 3mf mesh writer should not close the archive just yet (we still need to add stuff to it).
        mesh_writer.setStoreArchive(True)
        if not mesh_writer.write(stream, nodes, mode, self._ucp_model):
            self.setInformation(mesh_writer.getInformation())
            return False

        archive = mesh_writer.getArchive()
        if archive is None:  # This happens if there was no mesh data to write.
            archive = zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED)

        try:
            # Add global container stack data to the archive.
            self._writeContainerToArchive(global_stack, archive)

            # Also write all containers in the stack to the file
            for container in global_stack.getContainers():
                self._writeContainerToArchive(container, archive)

            # Check if the machine has extruders and save all that data as well.
            for extruder_stack in global_stack.extruderList:
                self._writeContainerToArchive(extruder_stack, archive)
                for container in extruder_stack.getContainers():
                    self._writeContainerToArchive(container, archive)

            # Write user settings data
            if self._ucp_model is not None:
                user_settings_data = self._getUserSettings(self._ucp_model)
                ThreeMFWriter._storeMetadataJson(user_settings_data, archive, USER_SETTINGS_PATH)
        except PermissionError:
            self.setInformation(catalog.i18nc("@error:zip", "No permission to write the workspace here."))
            Logger.error("No permission to write workspace to this stream.")
            return False

        # Write preferences to archive
        original_preferences = Application.getInstance().getPreferences()  # Copy only the preferences that we use to the workspace.
        temp_preferences = Preferences()
        for preference in {"general/visible_settings", "cura/active_mode", "cura/categories_expanded",
                           "metadata/setting_version"}:
            temp_preferences.addPreference(preference, None)
            temp_preferences.setValue(preference, original_preferences.getValue(preference))
        preferences_string = StringIO()
        temp_preferences.writeToFile(preferences_string)
        preferences_file = zipfile.ZipInfo("Cura/preferences.cfg")
        try:
            archive.writestr(preferences_file, preferences_string.getvalue())

            # Save Cura version
            version_file = zipfile.ZipInfo("Cura/version.ini")
            version_config_parser = configparser.ConfigParser(interpolation=None)
            version_config_parser.add_section("versions")
            version_config_parser.set("versions", "cura_version", application.getVersion())
            version_config_parser.set("versions", "build_type", application.getBuildType())
            version_config_parser.set("versions", "is_debug_mode", str(application.getIsDebugMode()))

            version_file_string = StringIO()
            version_config_parser.write(version_file_string)
            archive.writestr(version_file, version_file_string.getvalue())

            self._writePluginMetadataToArchive(archive)

            # Close the archive & reset states.
            archive.close()
        except PermissionError:
            self.setInformation(catalog.i18nc("@error:zip", "No permission to write the workspace here."))
            Logger.error("No permission to write workspace to this stream.")
            return False
        except EnvironmentError as e:
            self.setInformation(catalog.i18nc("@error:zip", str(e)))
            Logger.error("EnvironmentError when writing workspace to this stream: {err}".format(err=str(e)))
            return False
        mesh_writer.setStoreArchive(False)

        return True

    def write(self, stream, nodes, mode=WorkspaceWriter.OutputMode.BinaryMode):
        success = self._write(stream, nodes, mode=WorkspaceWriter.OutputMode.BinaryMode)
        self._ucp_model = None
        return success

    @staticmethod
    def _writePluginMetadataToArchive(archive: zipfile.ZipFile) -> None:
        file_name_template = "%s/plugin_metadata.json"

        for plugin_id, metadata in Application.getInstance().getWorkspaceMetadataStorage().getAllData().items():
            file_name = file_name_template % plugin_id
            file_in_archive = zipfile.ZipInfo(file_name)
            # We have to set the compress type of each file as well (it doesn't keep the type of the entire archive)
            file_in_archive.compress_type = zipfile.ZIP_DEFLATED
            import json
            archive.writestr(file_in_archive, json.dumps(metadata, separators = (", ", ": "), indent = 4, skipkeys = True))

    @staticmethod
    def _writeContainerToArchive(container, archive):
        """Helper function that writes ContainerStacks, InstanceContainers and DefinitionContainers to the archive.

        :param container: That follows the :type{ContainerInterface} to archive.
        :param archive: The archive to write to.
        """
        if isinstance(container, type(ContainerRegistry.getInstance().getEmptyInstanceContainer())):
            return  # Empty file, do nothing.

        file_suffix = ContainerRegistry.getMimeTypeForContainer(type(container)).preferredSuffix

        # Some containers have a base file, which should then be the file to use.
        if "base_file" in container.getMetaData():
            base_file = container.getMetaDataEntry("base_file")
            if base_file != container.getId():
                container = ContainerRegistry.getInstance().findContainers(id = base_file)[0]

        file_name = "Cura/%s.%s" % (container.getId(), file_suffix)

        try:
            if file_name in archive.namelist():
                return  # File was already saved, no need to do it again. Uranium guarantees unique ID's, so this should hold.

            file_in_archive = zipfile.ZipInfo(file_name)
            # For some reason we have to set the compress type of each file as well (it doesn't keep the type of the entire archive)
            file_in_archive.compress_type = zipfile.ZIP_DEFLATED

            # Do not include the network authentication keys
            ignore_keys = {
                "um_cloud_cluster_id",
                "um_network_key",
                "um_linked_to_account",
                "removal_warning",
                "host_guid",
                "group_name",
                "group_size",
                "connection_type",
                "capabilities",
                "octoprint_api_key",
                "is_online",
            }
            serialized_data = container.serialize(ignored_metadata_keys = ignore_keys)

            archive.writestr(file_in_archive, serialized_data)
        except (FileNotFoundError, EnvironmentError):
            Logger.error("File became inaccessible while writing to it: {archive_filename}".format(archive_filename = archive.fp.name))
            return

    @staticmethod
    def _getUserSettings(model: SettingsExportModel) -> Dict[str, Dict[str, Any]]:
        user_settings = {}

        for group in model.settingsGroups:
            category = ''
            if group.category == SettingsExportGroup.Category.Global:
                category = 'global'
            elif group.category == SettingsExportGroup.Category.Extruder:
                category = f"extruder_{group.extruder_index}"

            if len(category) > 0:
                settings_values = {}
                stack = group.stack

                for setting in group.settings:
                    if setting.selected:
                        settings_values[setting.id] = stack.getProperty(setting.id, "value")

                user_settings[category] = settings_values

        return user_settings