# Copyright (c) 2016 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

import os
from PyQt5.QtWidgets import QMessageBox

from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Application import Application
from UM.Logger import Logger
from UM.Message import Message
from UM.Platform import Platform
from UM.PluginRegistry import PluginRegistry #For getting the possible profile writers to write with.
from UM.Util import parseBool

from UM.i18n import i18nCatalog
catalog = i18nCatalog("uranium")

class CuraContainerRegistry(ContainerRegistry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    ##  Exports an profile to a file
    #
    #   \param instance_id \type{str} the ID of the profile to export.
    #   \param file_name \type{str} the full path and filename to export to.
    #   \param file_type \type{str} the file type with the format "<description> (*.<extension>)"
    def exportProfile(self, instance_id, file_name, file_type):
        Logger.log('d', 'exportProfile instance_id: '+str(instance_id))

        # Parse the fileType to deduce what plugin can save the file format.
        # fileType has the format "<description> (*.<extension>)"
        split = file_type.rfind(" (*.")  # Find where the description ends and the extension starts.
        if split < 0:  # Not found. Invalid format.
            Logger.log("e", "Invalid file format identifier %s", file_type)
            return
        description = file_type[:split]
        extension = file_type[split + 4:-1]  # Leave out the " (*." and ")".
        if not file_name.endswith("." + extension):  # Auto-fill the extension if the user did not provide any.
            file_name += "." + extension

        # On Windows, QML FileDialog properly asks for overwrite confirm, but not on other platforms, so handle those ourself.
        if not Platform.isWindows():
            if os.path.exists(file_name):
                result = QMessageBox.question(None, catalog.i18nc("@title:window", "File Already Exists"),
                                              catalog.i18nc("@label", "The file <filename>{0}</filename> already exists. Are you sure you want to overwrite it?").format(file_name))
                if result == QMessageBox.No:
                    return

        containers = ContainerRegistry.getInstance().findInstanceContainers(id=instance_id)
        if not containers:
            return
        container = containers[0]

        profile_writer = self._findProfileWriter(extension, description)

        try:
            success = profile_writer.write(file_name, container)
        except Exception as e:
            Logger.log("e", "Failed to export profile to %s: %s", file_name, str(e))
            m = Message(catalog.i18nc("@info:status", "Failed to export profile to <filename>{0}</filename>: <message>{1}</message>", file_name, str(e)), lifetime = 0)
            m.show()
            return
        if not success:
            Logger.log("w", "Failed to export profile to %s: Writer plugin reported failure.", file_name)
            m = Message(catalog.i18nc("@info:status", "Failed to export profile to <filename>{0}</filename>: Writer plugin reported failure.", file_name), lifetime = 0)
            m.show()
            return
        m = Message(catalog.i18nc("@info:status", "Exported profile to <filename>{0}</filename>", file_name))
        m.show()

    ##  Gets the plugin object matching the criteria
    #   \param extension
    #   \param description
    #   \return The plugin object matching the given extension and description.
    def _findProfileWriter(self, extension, description):
        pr = PluginRegistry.getInstance()
        for plugin_id, meta_data in self._getIOPlugins("profile_writer"):
            for supported_type in meta_data["profile_writer"]:  # All file types this plugin can supposedly write.
                supported_extension = supported_type.get("extension", None)
                if supported_extension == extension:  # This plugin supports a file type with the same extension.
                    supported_description = supported_type.get("description", None)
                    if supported_description == description:  # The description is also identical. Assume it's the same file type.
                        return pr.getPluginObject(plugin_id)
        return None

    ##  Imports a profile from a file
    #
    #   \param file_name \type{str} the full path and filename of the profile to import
    #   \return \type{Dict} dict with a 'status' key containing the string 'ok' or 'error', and a 'message' key
    #       containing a message for the user
    def importProfile(self, file_name):
        if not file_name:
            return { "status": "error", "message": catalog.i18nc("@info:status", "Failed to import profile from <filename>{0}</filename>: <message>{1}</message>", file_name, "Invalid path")}

        pr = PluginRegistry.getInstance()
        for plugin_id, meta_data in self._getIOPlugins("profile_reader"):
            profile_reader = pr.getPluginObject(plugin_id)
            try:
                profile = profile_reader.read(file_name) #Try to open the file with the profile reader.
            except Exception as e:
                #Note that this will fail quickly. That is, if any profile reader throws an exception, it will stop reading. It will only continue reading if the reader returned None.
                Logger.log("e", "Failed to import profile from %s: %s", file_name, str(e))
                return { "status": "error", "message": catalog.i18nc("@info:status", "Failed to import profile from <filename>{0}</filename>: <message>{1}</message>", file_name, str(e))}
            if profile: #Success!
                profile.setReadOnly(False)

                if self._machineHasOwnQualities():
                    profile.setDefinition(self._activeDefinition())
                    if self._machineHasOwnMaterials():
                        profile.addMetaDataEntry("material", self._activeMaterialId())
                else:
                    profile.setDefinition(ContainerRegistry.getInstance().findDefinitionContainers(id="fdmprinter")[0])
                ContainerRegistry.getInstance().addContainer(profile)

                return { "status": "ok", "message": catalog.i18nc("@info:status", "Successfully imported profile {0}", profile.getName()) }

        #If it hasn't returned by now, none of the plugins loaded the profile successfully.
        return { "status": "error", "message": catalog.i18nc("@info:status", "Profile {0} has an unknown file type.", file_name)}

    ##  Gets a list of profile writer plugins
    #   \return List of tuples of (plugin_id, meta_data).
    def _getIOPlugins(self, io_type):
        pr = PluginRegistry.getInstance()
        active_plugin_ids = pr.getActivePlugins()

        result = []
        for plugin_id in active_plugin_ids:
            meta_data = pr.getMetaData(plugin_id)
            if io_type in meta_data:
                result.append( (plugin_id, meta_data) )
        return result

    ##  Gets the active definition
    #   \return the active definition object or None if there is no definition
    def _activeDefinition(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            definition = global_container_stack.getBottom()
            if definition:
                return definition
        return None

    ##  Returns true if the current machine requires its own materials
    #   \return True if the current machine requires its own materials
    def _machineHasOwnMaterials(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            return global_container_stack.getMetaDataEntry("has_materials", False)
        return False

    ##  Gets the ID of the active material
    #   \return the ID of the active material or the empty string
    def _activeMaterialId(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            material = global_container_stack.findContainer({"type": "material"})
            if material:
                return material.getId()
        return ""

    ##  Returns true if the current machien requires its own quality profiles
    #   \return true if the current machien requires its own quality profiles
    def _machineHasOwnQualities(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            return parseBool(global_container_stack.getMetaDataEntry("has_machine_quality", False))
        return False
