# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os
import os.path
import re
import configparser

from typing import Optional

from PyQt5.QtWidgets import QMessageBox

from UM.Decorators import override
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.ContainerStack import ContainerStack
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Application import Application
from UM.Logger import Logger
from UM.Message import Message
from UM.Platform import Platform
from UM.PluginRegistry import PluginRegistry  # For getting the possible profile writers to write with.
from UM.Util import parseBool
from UM.Resources import Resources

from . import ExtruderStack
from . import GlobalStack
from .ContainerManager import ContainerManager
from .ExtruderManager import ExtruderManager

from cura.CuraApplication import CuraApplication

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

class CuraContainerRegistry(ContainerRegistry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    ##  Overridden from ContainerRegistry
    #
    #   Adds a container to the registry.
    #
    #   This will also try to convert a ContainerStack to either Extruder or
    #   Global stack based on metadata information.
    @override(ContainerRegistry)
    def addContainer(self, container):

        # Note: Intentional check with type() because we want to ignore subclasses
        if type(container) == ContainerStack:
            container = self._convertContainerStack(container)

        if isinstance(container, InstanceContainer) and type(container) != type(self.getEmptyInstanceContainer()):
            # Check against setting version of the definition.
            required_setting_version = CuraApplication.SettingVersion
            actual_setting_version = int(container.getMetaDataEntry("setting_version", default = 0))
            if required_setting_version != actual_setting_version:
                Logger.log("w", "Instance container {container_id} is outdated. Its setting version is {actual_setting_version} but it should be {required_setting_version}.".format(container_id = container.getId(), actual_setting_version = actual_setting_version, required_setting_version = required_setting_version))
                return #Don't add.

        super().addContainer(container)

    ##  Create a name that is not empty and unique
    #   \param container_type \type{string} Type of the container (machine, quality, ...)
    #   \param current_name \type{} Current name of the container, which may be an acceptable option
    #   \param new_name \type{string} Base name, which may not be unique
    #   \param fallback_name \type{string} Name to use when (stripped) new_name is empty
    #   \return \type{string} Name that is unique for the specified type and name/id
    def createUniqueName(self, container_type, current_name, new_name, fallback_name):
        new_name = new_name.strip()
        num_check = re.compile("(.*?)\s*#\d+$").match(new_name)
        if num_check:
            new_name = num_check.group(1)
        if new_name == "":
            new_name = fallback_name

        unique_name = new_name
        i = 1
        # In case we are renaming, the current name of the container is also a valid end-result
        while self._containerExists(container_type, unique_name) and unique_name != current_name:
            i += 1
            unique_name = "%s #%d" % (new_name, i)

        return unique_name

    ##  Check if a container with of a certain type and a certain name or id exists
    #   Both the id and the name are checked, because they may not be the same and it is better if they are both unique
    #   \param container_type \type{string} Type of the container (machine, quality, ...)
    #   \param container_name \type{string} Name to check
    def _containerExists(self, container_type, container_name):
        container_class = ContainerStack if container_type == "machine" else InstanceContainer

        return self.findContainers(container_class, id = container_name, type = container_type, ignore_case = True) or \
                self.findContainers(container_class, name = container_name, type = container_type)

    ##  Exports an profile to a file
    #
    #   \param instance_ids \type{list} the IDs of the profiles to export.
    #   \param file_name \type{str} the full path and filename to export to.
    #   \param file_type \type{str} the file type with the format "<description> (*.<extension>)"
    def exportProfile(self, instance_ids, file_name, file_type):
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
                                              catalog.i18nc("@label Don't translate the XML tag <filename>!", "The file <filename>{0}</filename> already exists. Are you sure you want to overwrite it?").format(file_name))
                if result == QMessageBox.No:
                    return
        found_containers = []
        extruder_positions = []
        for instance_id in instance_ids:
            containers = ContainerRegistry.getInstance().findInstanceContainers(id=instance_id)
            if containers:
                found_containers.append(containers[0])

                # Determine the position of the extruder of this container
                extruder_id = containers[0].getMetaDataEntry("extruder", "")
                if extruder_id == "":
                    # Global stack
                    extruder_positions.append(-1)
                else:
                    extruder_containers = ContainerRegistry.getInstance().findDefinitionContainers(id=extruder_id)
                    if extruder_containers:
                        extruder_positions.append(int(extruder_containers[0].getMetaDataEntry("position", 0)))
                    else:
                        extruder_positions.append(0)
        # Ensure the profiles are always exported in order (global, extruder 0, extruder 1, ...)
        found_containers = [containers for (positions, containers) in sorted(zip(extruder_positions, found_containers))]

        profile_writer = self._findProfileWriter(extension, description)

        try:
            success = profile_writer.write(file_name, found_containers)
        except Exception as e:
            Logger.log("e", "Failed to export profile to %s: %s", file_name, str(e))
            m = Message(catalog.i18nc("@info:status Don't translate the XML tags <filename> or <message>!", "Failed to export profile to <filename>{0}</filename>: <message>{1}</message>", file_name, str(e)),
                        lifetime = 0,
                        title = catalog.i18nc("@info:title", "Error"))
            m.show()
            return
        if not success:
            Logger.log("w", "Failed to export profile to %s: Writer plugin reported failure.", file_name)
            m = Message(catalog.i18nc("@info:status Don't translate the XML tag <filename>!", "Failed to export profile to <filename>{0}</filename>: Writer plugin reported failure.", file_name),
                        lifetime = 0,
                        title = catalog.i18nc("@info:title", "Error"))
            m.show()
            return
        m = Message(catalog.i18nc("@info:status Don't translate the XML tag <filename>!", "Exported profile to <filename>{0}</filename>", file_name),
                    title = catalog.i18nc("@info:title", "Export succeeded"))
        m.show()

    ##  Gets the plugin object matching the criteria
    #   \param extension
    #   \param description
    #   \return The plugin object matching the given extension and description.
    def _findProfileWriter(self, extension, description):
        plugin_registry = PluginRegistry.getInstance()
        for plugin_id, meta_data in self._getIOPlugins("profile_writer"):
            for supported_type in meta_data["profile_writer"]:  # All file types this plugin can supposedly write.
                supported_extension = supported_type.get("extension", None)
                if supported_extension == extension:  # This plugin supports a file type with the same extension.
                    supported_description = supported_type.get("description", None)
                    if supported_description == description:  # The description is also identical. Assume it's the same file type.
                        return plugin_registry.getPluginObject(plugin_id)
        return None

    ##  Imports a profile from a file
    #
    #   \param file_name \type{str} the full path and filename of the profile to import
    #   \return \type{Dict} dict with a 'status' key containing the string 'ok' or 'error', and a 'message' key
    #       containing a message for the user
    def importProfile(self, file_name):
        Logger.log("d", "Attempting to import profile %s", file_name)
        if not file_name:
            return { "status": "error", "message": catalog.i18nc("@info:status Don't translate the XML tags <filename> or <message>!", "Failed to import profile from <filename>{0}</filename>: <message>{1}</message>", file_name, "Invalid path")}

        plugin_registry = PluginRegistry.getInstance()
        extension = file_name.split(".")[-1]

        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if not global_container_stack:
            return

        machine_extruders = list(ExtruderManager.getInstance().getMachineExtruders(global_container_stack.getId()))
        machine_extruders.sort(key = lambda k: k.getMetaDataEntry("position"))

        for plugin_id, meta_data in self._getIOPlugins("profile_reader"):
            if meta_data["profile_reader"][0]["extension"] != extension:
                continue

            profile_reader = plugin_registry.getPluginObject(plugin_id)
            try:
                profile_or_list = profile_reader.read(file_name)  # Try to open the file with the profile reader.
            except Exception as e:
                # Note that this will fail quickly. That is, if any profile reader throws an exception, it will stop reading. It will only continue reading if the reader returned None.
                Logger.log("e", "Failed to import profile from %s: %s while using profile reader. Got exception %s", file_name,profile_reader.getPluginId(), str(e))
                return { "status": "error", "message": catalog.i18nc("@info:status Don't translate the XML tags <filename> or <message>!", "Failed to import profile from <filename>{0}</filename>: <message>{1}</message>", file_name, str(e))}

            if profile_or_list:
                name_seed = os.path.splitext(os.path.basename(file_name))[0]
                new_name = self.uniqueName(name_seed)

                # Ensure it is always a list of profiles
                if type(profile_or_list) is not list:
                    profile_or_list = [profile_or_list]

                if len(profile_or_list) == 1:
                    # If there is only 1 stack file it means we're loading a legacy (pre-3.1) .curaprofile.
                    # In that case we find the per-extruder settings and put those in a new quality_changes container
                    # so that it is compatible with the new stack setup.
                    profile = profile_or_list[0]
                    extruder_stack_quality_changes_container = ContainerManager.getInstance().duplicateContainerInstance(profile)
                    extruder_stack_quality_changes_container.addMetaDataEntry("extruder", "fdmextruder")

                    for quality_changes_setting_key in extruder_stack_quality_changes_container.getAllKeys():
                        settable_per_extruder = extruder_stack_quality_changes_container.getProperty(quality_changes_setting_key, "settable_per_extruder")
                        if settable_per_extruder:
                            profile.removeInstance(quality_changes_setting_key, postpone_emit = True)
                        else:
                            extruder_stack_quality_changes_container.removeInstance(quality_changes_setting_key, postpone_emit = True)

                    # We add the new container to the profile list so things like extruder positions are taken care of
                    # in the next code segment.
                    profile_or_list.append(extruder_stack_quality_changes_container)

                # Import all profiles
                for profile_index, profile in enumerate(profile_or_list):
                    if profile_index == 0:
                        # This is assumed to be the global profile
                        profile_id = (global_container_stack.getBottom().getId() + "_" + name_seed).lower().replace(" ", "_")

                    elif len(machine_extruders) > profile_index:
                        # This is assumed to be an extruder profile
                        extruder_id = Application.getInstance().getMachineManager().getQualityDefinitionId(machine_extruders[profile_index - 1].getBottom())
                        if not profile.getMetaDataEntry("extruder"):
                            profile.addMetaDataEntry("extruder", extruder_id)
                        else:
                            profile.setMetaDataEntry("extruder", extruder_id)
                        profile_id = (extruder_id + "_" + name_seed).lower().replace(" ", "_")

                    result = self._configureProfile(profile, profile_id, new_name)
                    if result is not None:
                        return {"status": "error", "message": catalog.i18nc(
                            "@info:status Don't translate the XML tags <filename> or <message>!",
                            "Failed to import profile from <filename>{0}</filename>: <message>{1}</message>",
                            file_name, result)}

                return {"status": "ok", "message": catalog.i18nc("@info:status", "Successfully imported profile {0}", profile_or_list[0].getName())}

        # If it hasn't returned by now, none of the plugins loaded the profile successfully.
        return {"status": "error", "message": catalog.i18nc("@info:status", "Profile {0} has an unknown file type or is corrupted.", file_name)}

    @override(ContainerRegistry)
    def load(self):
        super().load()
        self._registerSingleExtrusionMachinesExtruderStacks()
        self._connectUpgradedExtruderStacksToMachines()

    ##  Update an imported profile to match the current machine configuration.
    #
    #   \param profile The profile to configure.
    #   \param id_seed The base ID for the profile. May be changed so it does not conflict with existing containers.
    #   \param new_name The new name for the profile.
    #
    #   \return None if configuring was successful or an error message if an error occurred.
    def _configureProfile(self, profile: InstanceContainer, id_seed: str, new_name: str) -> Optional[str]:
        profile.setReadOnly(False)
        profile.setDirty(True)  # Ensure the profiles are correctly saved

        new_id = self.createUniqueName("quality_changes", "", id_seed, catalog.i18nc("@label", "Custom profile"))
        profile._id = new_id
        profile.setName(new_name)

        if "type" in profile.getMetaData():
            profile.setMetaDataEntry("type", "quality_changes")
        else:
            profile.addMetaDataEntry("type", "quality_changes")

        quality_type = profile.getMetaDataEntry("quality_type")
        if not quality_type:
            return catalog.i18nc("@info:status", "Profile is missing a quality type.")

        quality_type_criteria = {"quality_type": quality_type}
        if self._machineHasOwnQualities():
            profile.setDefinition(self._activeQualityDefinition())
            if self._machineHasOwnMaterials():
                active_material_id = self._activeMaterialId()
                if active_material_id and active_material_id != "empty":  # only update if there is an active material
                    profile.addMetaDataEntry("material", active_material_id)
                    quality_type_criteria["material"] = active_material_id

            quality_type_criteria["definition"] = profile.getDefinition().getId()

        else:
            profile.setDefinition(ContainerRegistry.getInstance().findDefinitionContainers(id="fdmprinter")[0])
            quality_type_criteria["definition"] = "fdmprinter"

        machine_definition = Application.getInstance().getGlobalContainerStack().getBottom()
        del quality_type_criteria["definition"]

        # materials = None

        if "material" in quality_type_criteria:
            # materials = ContainerRegistry.getInstance().findInstanceContainers(id = quality_type_criteria["material"])
            del quality_type_criteria["material"]

        # Do not filter quality containers here with materials because we are trying to import a profile, so it should
        # NOT be restricted by the active materials on the current machine.
        materials = None

        # Check to make sure the imported profile actually makes sense in context of the current configuration.
        # This prevents issues where importing a "draft" profile for a machine without "draft" qualities would report as
        # successfully imported but then fail to show up.
        from cura.QualityManager import QualityManager
        qualities = QualityManager.getInstance()._getFilteredContainersForStack(machine_definition, materials, **quality_type_criteria)
        if not qualities:
            return catalog.i18nc("@info:status", "Could not find a quality type {0} for the current configuration.", quality_type)

        ContainerRegistry.getInstance().addContainer(profile)

        return None

    ##  Gets a list of profile writer plugins
    #   \return List of tuples of (plugin_id, meta_data).
    def _getIOPlugins(self, io_type):
        plugin_registry = PluginRegistry.getInstance()
        active_plugin_ids = plugin_registry.getActivePlugins()

        result = []
        for plugin_id in active_plugin_ids:
            meta_data = plugin_registry.getMetaData(plugin_id)
            if io_type in meta_data:
                result.append( (plugin_id, meta_data) )
        return result

    ##  Get the definition to use to select quality profiles for the active machine
    #   \return the active quality definition object or None if there is no quality definition
    def _activeQualityDefinition(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            definition_id = Application.getInstance().getMachineManager().getQualityDefinitionId(global_container_stack.getBottom())
            definition = self.findDefinitionContainers(id=definition_id)[0]

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
        if global_container_stack and global_container_stack.material:
            return global_container_stack.material.getId()
        return ""

    ##  Returns true if the current machine requires its own quality profiles
    #   \return true if the current machine requires its own quality profiles
    def _machineHasOwnQualities(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            return parseBool(global_container_stack.getMetaDataEntry("has_machine_quality", False))
        return False

    ##  Convert an "old-style" pure ContainerStack to either an Extruder or Global stack.
    def _convertContainerStack(self, container):
        assert type(container) == ContainerStack

        container_type = container.getMetaDataEntry("type")
        if container_type not in ("extruder_train", "machine"):
            # It is not an extruder or machine, so do nothing with the stack
            return container

        Logger.log("d", "Converting ContainerStack {stack} to {type}", stack = container.getId(), type = container_type)

        new_stack = None
        if container_type == "extruder_train":
            new_stack = ExtruderStack.ExtruderStack(container.getId())
        else:
            new_stack = GlobalStack.GlobalStack(container.getId())

        container_contents = container.serialize()
        new_stack.deserialize(container_contents)

        # Delete the old configuration file so we do not get double stacks
        if os.path.isfile(container.getPath()):
            os.remove(container.getPath())

        return new_stack

    def _registerSingleExtrusionMachinesExtruderStacks(self):
        machines = self.findContainerStacks(type = "machine", machine_extruder_trains = {"0": "fdmextruder"})
        for machine in machines:
            extruder_stacks = self.findContainerStacks(type = "extruder_train", machine = machine.getId())
            if not extruder_stacks:
                self.addExtruderStackForSingleExtrusionMachine(machine, "fdmextruder")

    def addExtruderStackForSingleExtrusionMachine(self, machine, extruder_id):
        new_extruder_id = extruder_id

        extruder_definitions = self.findDefinitionContainers(id = new_extruder_id)
        if not extruder_definitions:
            Logger.log("w", "Could not find definition containers for extruder %s", new_extruder_id)
            return

        extruder_definition = extruder_definitions[0]
        unique_name = self.uniqueName(machine.getName() + " " + new_extruder_id)

        extruder_stack = ExtruderStack.ExtruderStack(unique_name)
        extruder_stack.setName(extruder_definition.getName())
        extruder_stack.setDefinition(extruder_definition)
        extruder_stack.addMetaDataEntry("position", extruder_definition.getMetaDataEntry("position"))
        extruder_stack.setNextStack(machine)

        # create empty user changes container otherwise
        user_container = InstanceContainer(extruder_stack.id + "_user")
        user_container.addMetaDataEntry("type", "user")
        user_container.addMetaDataEntry("machine", extruder_stack.getId())
        from cura.CuraApplication import CuraApplication
        user_container.addMetaDataEntry("setting_version", CuraApplication.SettingVersion)
        user_container.setDefinition(machine.definition)

        if machine.userChanges:
            # for the newly created extruder stack, we need to move all "per-extruder" settings to the user changes
            # container to the extruder stack.
            for user_setting_key in machine.userChanges.getAllKeys():
                settable_per_extruder = machine.getProperty(user_setting_key, "settable_per_extruder")
                if settable_per_extruder:
                    user_container.addInstance(machine.userChanges.getInstance(user_setting_key))
                    machine.userChanges.removeInstance(user_setting_key, postpone_emit = True)

        extruder_stack.setUserChanges(user_container)
        self.addContainer(user_container)

        variant_id = "default"
        if machine.variant.getId() not in ("empty", "empty_variant"):
            variant_id = machine.variant.getId()
        else:
            variant_id = "empty_variant"
        extruder_stack.setVariantById(variant_id)

        material_id = "default"
        if machine.material.getId() not in ("empty", "empty_material"):
            material_id = machine.material.getId()
        else:
            material_id = "empty_material"
        extruder_stack.setMaterialById(material_id)

        quality_id = "default"
        if machine.quality.getId() not in ("empty", "empty_quality"):
            quality_id = machine.quality.getId()
        else:
            quality_id = "empty_quality"
        extruder_stack.setQualityById(quality_id)

        if machine.qualityChanges.getId() not in ("empty", "empty_quality_changes"):
            extruder_quality_changes_container = self.findInstanceContainers(name = machine.qualityChanges.getName(), extruder = extruder_id)
            if extruder_quality_changes_container:
                extruder_quality_changes_container = extruder_quality_changes_container[0]
                quality_changes_id = extruder_quality_changes_container.getId()
                extruder_stack.setQualityChangesById(quality_changes_id)
            else:
                # Some extruder quality_changes containers can be created at runtime as files in the qualities
                # folder. Those files won't be loaded in the registry immediately. So we also need to search
                # the folder to see if the quality_changes exists.
                extruder_quality_changes_container = self._findQualityChangesContainerInCuraFolder(machine.qualityChanges.getName())
                if extruder_quality_changes_container:
                    quality_changes_id = extruder_quality_changes_container.getId()
                    extruder_stack.setQualityChangesById(quality_changes_id)

            if not extruder_quality_changes_container:
                Logger.log("w", "Could not find quality_changes named [%s] for extruder [%s]",
                           machine.qualityChanges.getName(), extruder_stack.getId())
        else:
            extruder_stack.setQualityChangesById("empty_quality_changes")

        self.addContainer(extruder_stack)

        return extruder_stack

    def _findQualityChangesContainerInCuraFolder(self, name):
        quality_changes_dir = Resources.getPath(CuraApplication.ResourceTypes.QualityInstanceContainer)

        instance_container = None

        for item in os.listdir(quality_changes_dir):
            file_path = os.path.join(quality_changes_dir, item)
            if not os.path.isfile(file_path):
                continue

            parser = configparser.ConfigParser()
            try:
                parser.read([file_path])
            except:
                # skip, it is not a valid stack file
                continue

            if not parser.has_option("general", "name"):
                continue

            if parser["general"]["name"] == name:
                # load the container
                container_id = os.path.basename(file_path).replace(".inst.cfg", "")

                instance_container = InstanceContainer(container_id)
                with open(file_path, "r") as f:
                    serialized = f.read()
                instance_container.deserialize(serialized, file_path)
                self.addContainer(instance_container)
                break

        return instance_container

    # Fix the extruders that were upgraded to ExtruderStack instances during addContainer.
    # The stacks are now responsible for setting the next stack on deserialize. However,
    # due to problems with loading order, some stacks may not have the proper next stack
    # set after upgrading, because the proper global stack was not yet loaded. This method
    # makes sure those extruders also get the right stack set.
    def _connectUpgradedExtruderStacksToMachines(self):
        extruder_stacks = self.findContainers(ExtruderStack.ExtruderStack)
        for extruder_stack in extruder_stacks:
            if extruder_stack.getNextStack():
                # Has the right next stack, so ignore it.
                continue

            machines = ContainerRegistry.getInstance().findContainerStacks(id=extruder_stack.getMetaDataEntry("machine", ""))
            if machines:
                extruder_stack.setNextStack(machines[0])
            else:
                Logger.log("w", "Could not find machine {machine} for extruder {extruder}", machine = extruder_stack.getMetaDataEntry("machine"), extruder = extruder_stack.getId())
