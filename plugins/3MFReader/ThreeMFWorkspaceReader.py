# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Workspace.WorkspaceReader import WorkspaceReader
from UM.Application import Application

from UM.Logger import Logger
from UM.i18n import i18nCatalog
from UM.Settings.ContainerStack import ContainerStack
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.MimeTypeDatabase import MimeTypeDatabase
from UM.Job import Job
from UM.Preferences import Preferences
from .WorkspaceDialog import WorkspaceDialog

import xml.etree.ElementTree as ET

from cura.Settings.ExtruderManager import ExtruderManager
from cura.Settings.ExtruderStack import ExtruderStack
from cura.Settings.GlobalStack import GlobalStack

from configparser import ConfigParser
import zipfile
import io
import configparser

i18n_catalog = i18nCatalog("cura")


##    Base implementation for reading 3MF workspace files.
class ThreeMFWorkspaceReader(WorkspaceReader):
    def __init__(self):
        super().__init__()
        self._supported_extensions = [".3mf"]
        self._dialog = WorkspaceDialog()
        self._3mf_mesh_reader = None
        self._container_registry = ContainerRegistry.getInstance()

        # suffixes registered with the MineTypes don't start with a dot '.'
        self._definition_container_suffix = "." + ContainerRegistry.getMimeTypeForContainer(DefinitionContainer).preferredSuffix
        self._material_container_suffix = None # We have to wait until all other plugins are loaded before we can set it
        self._instance_container_suffix = "." + ContainerRegistry.getMimeTypeForContainer(InstanceContainer).preferredSuffix
        self._container_stack_suffix = "." + ContainerRegistry.getMimeTypeForContainer(ContainerStack).preferredSuffix
        self._extruder_stack_suffix = "." + ContainerRegistry.getMimeTypeForContainer(ExtruderStack).preferredSuffix
        self._global_stack_suffix = "." + ContainerRegistry.getMimeTypeForContainer(GlobalStack).preferredSuffix

        # Certain instance container types are ignored because we make the assumption that only we make those types
        # of containers. They are:
        #  - quality
        #  - variant
        self._ignored_instance_container_types = {"quality", "variant"}

        self._resolve_strategies = {}

        self._id_mapping = {}

    ##  Get a unique name based on the old_id. This is different from directly calling the registry in that it caches results.
    #   This has nothing to do with speed, but with getting consistent new naming for instances & objects.
    def getNewId(self, old_id):
        if old_id not in self._id_mapping:
            self._id_mapping[old_id] = self._container_registry.uniqueName(old_id)
        return self._id_mapping[old_id]

    ##  Separates the given file list into a list of GlobalStack files and a list of ExtruderStack files.
    #
    #   In old versions, extruder stack files have the same suffix as container stack files ".stack.cfg".
    #
    def _determineGlobalAndExtruderStackFiles(self, project_file_name, file_list):
        archive = zipfile.ZipFile(project_file_name, "r")

        global_stack_file_list = [name for name in file_list if name.endswith(self._global_stack_suffix)]
        extruder_stack_file_list = [name for name in file_list if name.endswith(self._extruder_stack_suffix)]

        # separate container stack files and extruder stack files
        files_to_determine = [name for name in file_list if name.endswith(self._container_stack_suffix)]
        for file_name in files_to_determine:
            # FIXME: HACK!
            # We need to know the type of the stack file, but we can only know it if we deserialize it.
            # The default ContainerStack.deserialize() will connect signals, which is not desired in this case.
            # Since we know that the stack files are INI files, so we directly use the ConfigParser to parse them.
            serialized = archive.open(file_name).read().decode("utf-8")
            stack_config = ConfigParser()
            stack_config.read_string(serialized)

            # sanity check
            if not stack_config.has_option("metadata", "type"):
                Logger.log("e", "%s in %s doesn't seem to be valid stack file", file_name, project_file_name)
                continue

            stack_type = stack_config.get("metadata", "type")
            if stack_type == "extruder_train":
                extruder_stack_file_list.append(file_name)
            elif stack_type == "machine":
                global_stack_file_list.append(file_name)
            else:
                Logger.log("w", "Unknown container stack type '%s' from %s in %s",
                           stack_type, file_name, project_file_name)

        if len(global_stack_file_list) != 1:
            raise RuntimeError("More than one global stack file found: [%s]" % str(global_stack_file_list))

        return global_stack_file_list[0], extruder_stack_file_list

    ##  read some info so we can make decisions
    #   \param file_name
    #   \param show_dialog  In case we use preRead() to check if a file is a valid project file, we don't want to show a dialog.
    def preRead(self, file_name, show_dialog=True, *args, **kwargs):
        self._3mf_mesh_reader = Application.getInstance().getMeshFileHandler().getReaderForFile(file_name)
        if self._3mf_mesh_reader and self._3mf_mesh_reader.preRead(file_name) == WorkspaceReader.PreReadResult.accepted:
            pass
        else:
            Logger.log("w", "Could not find reader that was able to read the scene data for 3MF workspace")
            return WorkspaceReader.PreReadResult.failed

        machine_name = ""
        machine_type = ""
        variant_type_name = i18n_catalog.i18nc("@label", "Nozzle")

        # Check if there are any conflicts, so we can ask the user.
        archive = zipfile.ZipFile(file_name, "r")
        cura_file_names = [name for name in archive.namelist() if name.startswith("Cura/")]

        # A few lists of containers in this project files.
        # When loading the global stack file, it may be associated with those containers, which may or may not be
        # in Cura already, so we need to provide them as alternative search lists.
        definition_container_list = []
        instance_container_list = []
        material_container_list = []

        #
        # Read definition containers
        #
        machine_definition_container_count = 0
        extruder_definition_container_count = 0
        definition_container_files = [name for name in cura_file_names if name.endswith(self._definition_container_suffix)]
        for each_definition_container_file in definition_container_files:
            container_id = self._stripFileToId(each_definition_container_file)
            definitions = self._container_registry.findDefinitionContainers(id=container_id)

            if not definitions:
                definition_container = DefinitionContainer(container_id)
                definition_container.deserialize(archive.open(each_definition_container_file).read().decode("utf-8"))

            else:
                definition_container = definitions[0]
            definition_container_list.append(definition_container)

            definition_container_type = definition_container.getMetaDataEntry("type")
            if definition_container_type == "machine":
                machine_type = definition_container.getName()
                variant_type_name = definition_container.getMetaDataEntry("variants_name", variant_type_name)

                machine_definition_container_count += 1
            elif definition_container_type == "extruder":
                extruder_definition_container_count += 1
            else:
                Logger.log("w", "Unknown definition container type %s for %s",
                           definition_container_type, each_definition_container_file)
            Job.yieldThread()
        # sanity check
        if machine_definition_container_count != 1:
            msg = "Expecting one machine definition container but got %s" % machine_definition_container_count
            Logger.log("e", msg)
            raise RuntimeError(msg)

        material_labels = []
        material_conflict = False
        xml_material_profile = self._getXmlProfileClass()
        if self._material_container_suffix is None:
            self._material_container_suffix = ContainerRegistry.getMimeTypeForContainer(xml_material_profile).preferredSuffix
        if xml_material_profile:
            material_container_files = [name for name in cura_file_names if name.endswith(self._material_container_suffix)]
            for material_container_file in material_container_files:
                container_id = self._stripFileToId(material_container_file)
                materials = self._container_registry.findInstanceContainers(id=container_id)
                material_labels.append(self._getMaterialLabelFromSerialized(archive.open(material_container_file).read().decode("utf-8")))
                if materials and not materials[0].isReadOnly():  # Only non readonly materials can be in conflict
                    material_conflict = True
                Job.yieldThread()

        # Check if any quality_changes instance container is in conflict.
        instance_container_files = [name for name in cura_file_names if name.endswith(self._instance_container_suffix)]
        quality_name = ""
        quality_type = ""
        num_settings_overriden_by_quality_changes = 0 # How many settings are changed by the quality changes
        num_settings_overriden_by_definition_changes = 0 # How many settings are changed by the definition changes
        num_user_settings = 0
        quality_changes_conflict = False
        definition_changes_conflict = False

        for each_instance_container_file in instance_container_files:
            container_id = self._stripFileToId(each_instance_container_file)
            instance_container = InstanceContainer(container_id)

            # Deserialize InstanceContainer by converting read data from bytes to string
            instance_container.deserialize(archive.open(each_instance_container_file).read().decode("utf-8"))
            instance_container_list.append(instance_container)

            container_type = instance_container.getMetaDataEntry("type")
            if container_type == "quality_changes":
                quality_name = instance_container.getName()
                num_settings_overriden_by_quality_changes += len(instance_container._instances)
                # Check if quality changes already exists.
                quality_changes = self._container_registry.findInstanceContainers(id = container_id)
                if quality_changes:
                    # Check if there really is a conflict by comparing the values
                    if quality_changes[0] != instance_container:
                        quality_changes_conflict = True
            elif container_type == "definition_changes":
                definition_name = instance_container.getName()
                num_settings_overriden_by_definition_changes += len(instance_container._instances)
                definition_changes = self._container_registry.findDefinitionContainers(id = container_id)
                if definition_changes:
                    if definition_changes[0] != instance_container:
                        definition_changes_conflict = True
            elif container_type == "user":
                num_user_settings += len(instance_container._instances)
            elif container_type in self._ignored_instance_container_types:
                # Ignore certain instance container types
                Logger.log("w", "Ignoring instance container [%s] with type [%s]", container_id, container_type)
                continue

            Job.yieldThread()

        # Load ContainerStack files and ExtruderStack files
        global_stack_file, extruder_stack_files = self._determineGlobalAndExtruderStackFiles(
            file_name, cura_file_names)
        self._resolve_strategies = {"machine": None, "quality_changes": None, "material": None}
        machine_conflict = False
        for container_stack_file in [global_stack_file] + extruder_stack_files:
            container_id = self._stripFileToId(container_stack_file)
            serialized = archive.open(container_stack_file).read().decode("utf-8")
            if machine_name == "":
                machine_name = self._getMachineNameFromSerializedStack(serialized)
            stacks = self._container_registry.findContainerStacks(id = container_id)
            if stacks:
                # Check if there are any changes at all in any of the container stacks.
                id_list = self._getContainerIdListFromSerialized(serialized)
                for index, container_id in enumerate(id_list):
                    if stacks[0].getContainer(index).getId() != container_id:
                        machine_conflict = True
            Job.yieldThread()

        num_visible_settings = 0
        try:
            temp_preferences = Preferences()
            temp_preferences.readFromFile(io.TextIOWrapper(archive.open("Cura/preferences.cfg")))  # We need to wrap it, else the archive parser breaks.

            visible_settings_string = temp_preferences.getValue("general/visible_settings")
            if visible_settings_string is not None:
                num_visible_settings = len(visible_settings_string.split(";"))
            active_mode = temp_preferences.getValue("cura/active_mode")
            if not active_mode:
                active_mode = Preferences.getInstance().getValue("cura/active_mode")
        except KeyError:
            # If there is no preferences file, it's not a workspace, so notify user of failure.
            Logger.log("w", "File %s is not a valid workspace.", file_name)
            return WorkspaceReader.PreReadResult.failed

        # In case we use preRead() to check if a file is a valid project file, we don't want to show a dialog.
        if not show_dialog:
            return WorkspaceReader.PreReadResult.accepted

        # prepare data for the dialog
        num_extruders = extruder_definition_container_count
        if num_extruders == 0:
            num_extruders = 1  # No extruder stacks found, which means there is one extruder

        extruders = num_extruders * [""]

        # Show the dialog, informing the user what is about to happen.
        self._dialog.setMachineConflict(machine_conflict)
        self._dialog.setQualityChangesConflict(quality_changes_conflict)
        self._dialog.setDefinitionChangesConflict(definition_changes_conflict)
        self._dialog.setMaterialConflict(material_conflict)
        self._dialog.setNumVisibleSettings(num_visible_settings)
        self._dialog.setQualityName(quality_name)
        self._dialog.setQualityType(quality_type)
        self._dialog.setNumSettingsOverridenByQualityChanges(num_settings_overriden_by_quality_changes)
        self._dialog.setNumUserSettings(num_user_settings)
        self._dialog.setActiveMode(active_mode)
        self._dialog.setMachineName(machine_name)
        self._dialog.setMaterialLabels(material_labels)
        self._dialog.setMachineType(machine_type)
        self._dialog.setExtruders(extruders)
        self._dialog.setVariantType(variant_type_name)
        self._dialog.setHasObjectsOnPlate(Application.getInstance().platformActivity)
        self._dialog.show()

        # Block until the dialog is closed.
        self._dialog.waitForClose()

        if self._dialog.getResult() == {}:
            return WorkspaceReader.PreReadResult.cancelled

        self._resolve_strategies = self._dialog.getResult()
        #
        # There can be 3 resolve strategies coming from the dialog:
        #  - new:       create a new container
        #  - override:  override the existing container
        #  - None:      There is no conflict, which means containers with the same IDs may or may not be there already.
        #               If they are there, there is no conflict between the them.
        #               In this case, you can either create a new one, or safely override the existing one.
        #
        # Default values
        for k, v in self._resolve_strategies.items():
            if v is None:
                self._resolve_strategies[k] = "new"

        return WorkspaceReader.PreReadResult.accepted

    ## Overrides an ExtruderStack in the given GlobalStack and returns the new ExtruderStack.
    def _overrideExtruderStack(self, global_stack, extruder_index, extruder_file_content):
        extruder_index_str = str(extruder_index)

        extruder_stack = global_stack.extruders[extruder_index_str]
        old_extruder_stack_id = extruder_stack.getId()

        # override the given extruder stack
        extruder_stack.deserialize(extruder_file_content)

        # return the new ExtruderStack
        return extruder_stack

    ##  Read the project file
    #   Add all the definitions / materials / quality changes that do not exist yet. Then it loads
    #   all the stacks into the container registry. In some cases it will reuse the container for the global stack.
    #   It handles old style project files containing .stack.cfg as well as new style project files
    #   containing global.cfg / extruder.cfg
    #
    #   \param file_name
    def read(self, file_name):
        archive = zipfile.ZipFile(file_name, "r")

        cura_file_names = [name for name in archive.namelist() if name.startswith("Cura/")]

        # Create a shadow copy of the preferences (we don't want all of the preferences, but we do want to re-use its
        # parsing code.
        temp_preferences = Preferences()
        temp_preferences.readFromFile(io.TextIOWrapper(archive.open("Cura/preferences.cfg")))  # We need to wrap it, else the archive parser breaks.

        # Copy a number of settings from the temp preferences to the global
        global_preferences = Preferences.getInstance()

        visible_settings = temp_preferences.getValue("general/visible_settings")
        if visible_settings is None:
            Logger.log("w", "Workspace did not contain visible settings. Leaving visibility unchanged")
        else:
            global_preferences.setValue("general/visible_settings", visible_settings)

        categories_expanded = temp_preferences.getValue("cura/categories_expanded")
        if categories_expanded is None:
            Logger.log("w", "Workspace did not contain expanded categories. Leaving them unchanged")
        else:
            global_preferences.setValue("cura/categories_expanded", categories_expanded)

        Application.getInstance().expandedCategoriesChanged.emit()  # Notify the GUI of the change

        self._id_mapping = {}

        # We don't add containers right away, but wait right until right before the stack serialization.
        # We do this so that if something goes wrong, it's easier to clean up.
        containers_to_add = []

        global_stack_file, extruder_stack_files = self._determineGlobalAndExtruderStackFiles(file_name, cura_file_names)

        global_stack = None
        extruder_stacks = []
        extruder_stacks_added = []
        container_stacks_added = []

        containers_added = []

        global_stack_id_original = self._stripFileToId(global_stack_file)
        global_stack_id_new = global_stack_id_original
        global_stack_need_rename = False

        extruder_stack_id_map = {}  # new and old ExtruderStack IDs map
        if self._resolve_strategies["machine"] == "new":
            # We need a new id if the id already exists
            if self._container_registry.findContainerStacks(id = global_stack_id_original):
                global_stack_id_new = self.getNewId(global_stack_id_original)
                global_stack_need_rename = True

            for each_extruder_stack_file in extruder_stack_files:
                old_container_id = self._stripFileToId(each_extruder_stack_file)
                new_container_id = old_container_id
                if self._container_registry.findContainerStacks(id = old_container_id):
                    # get a new name for this extruder
                    new_container_id = self.getNewId(old_container_id)

                extruder_stack_id_map[old_container_id] = new_container_id

        # TODO: For the moment we use pretty naive existence checking. If the ID is the same, we assume in quite a few
        # TODO: cases that the container loaded is the same (most notable in materials & definitions).
        # TODO: It might be possible that we need to add smarter checking in the future.
        Logger.log("d", "Workspace loading is checking definitions...")
        # Get all the definition files & check if they exist. If not, add them.
        definition_container_files = [name for name in cura_file_names if name.endswith(self._definition_container_suffix)]
        for definition_container_file in definition_container_files:
            container_id = self._stripFileToId(definition_container_file)
            definitions = self._container_registry.findDefinitionContainers(id = container_id)
            if not definitions:
                definition_container = DefinitionContainer(container_id)
                definition_container.deserialize(archive.open(definition_container_file).read().decode("utf-8"))
                self._container_registry.addContainer(definition_container)
            Job.yieldThread()

        Logger.log("d", "Workspace loading is checking materials...")
        material_containers = []
        # Get all the material files and check if they exist. If not, add them.
        xml_material_profile = self._getXmlProfileClass()
        if self._material_container_suffix is None:
            self._material_container_suffix = ContainerRegistry.getMimeTypeForContainer(xml_material_profile).suffixes[0]
        if xml_material_profile:
            material_container_files = [name for name in cura_file_names if name.endswith(self._material_container_suffix)]
            for material_container_file in material_container_files:
                container_id = self._stripFileToId(material_container_file)
                materials = self._container_registry.findInstanceContainers(id = container_id)

                if not materials:
                    material_container = xml_material_profile(container_id)
                    material_container.deserialize(archive.open(material_container_file).read().decode("utf-8"))
                    containers_to_add.append(material_container)
                else:
                    material_container = materials[0]
                    if not material_container.isReadOnly():  # Only create new materials if they are not read only.
                        if self._resolve_strategies["material"] == "override":
                            material_container.deserialize(archive.open(material_container_file).read().decode("utf-8"))
                        elif self._resolve_strategies["material"] == "new":
                            # Note that we *must* deserialize it with a new ID, as multiple containers will be
                            # auto created & added.
                            material_container = xml_material_profile(self.getNewId(container_id))
                            material_container.deserialize(archive.open(material_container_file).read().decode("utf-8"))
                            containers_to_add.append(material_container)

                material_containers.append(material_container)
                Job.yieldThread()

        Logger.log("d", "Workspace loading is checking instance containers...")
        # Get quality_changes and user profiles saved in the workspace
        instance_container_files = [name for name in cura_file_names if name.endswith(self._instance_container_suffix)]
        user_instance_containers = []
        quality_and_definition_changes_instance_containers = []
        for instance_container_file in instance_container_files:
            container_id = self._stripFileToId(instance_container_file)
            serialized = archive.open(instance_container_file).read().decode("utf-8")

            # HACK! we ignore "quality" and "variant" instance containers!
            parser = configparser.ConfigParser()
            parser.read_string(serialized)
            if not parser.has_option("metadata", "type"):
                Logger.log("w", "Cannot find metadata/type in %s, ignoring it", instance_container_file)
                continue
            if parser.get("metadata", "type") in self._ignored_instance_container_types:
                continue

            instance_container = InstanceContainer(container_id)

            # Deserialize InstanceContainer by converting read data from bytes to string
            instance_container.deserialize(serialized)
            container_type = instance_container.getMetaDataEntry("type")
            Job.yieldThread()

            #
            # IMPORTANT:
            # If an instance container (or maybe other type of container) exists, and user chooses "Create New",
            # we need to rename this container and all references to it, and changing those references are VERY
            # HARD.
            #
            if container_type in self._ignored_instance_container_types:
                # Ignore certain instance container types
                Logger.log("w", "Ignoring instance container [%s] with type [%s]", container_id, container_type)
                continue
            elif container_type == "user":
                # Check if quality changes already exists.
                user_containers = self._container_registry.findInstanceContainers(id = container_id)
                if not user_containers:
                    containers_to_add.append(instance_container)
                else:
                    if self._resolve_strategies["machine"] == "override" or self._resolve_strategies["machine"] is None:
                        instance_container = user_containers[0]
                        instance_container.deserialize(archive.open(instance_container_file).read().decode("utf-8"))
                        instance_container.setDirty(True)
                    elif self._resolve_strategies["machine"] == "new":
                        # The machine is going to get a spiffy new name, so ensure that the id's of user settings match.
                        old_extruder_id = instance_container.getMetaDataEntry("extruder", None)
                        if old_extruder_id:
                            new_extruder_id = extruder_stack_id_map[old_extruder_id]
                            new_id = new_extruder_id + "_current_settings"
                            instance_container._id = new_id
                            instance_container.setName(new_id)
                            instance_container.setMetaDataEntry("extruder", new_extruder_id)
                            containers_to_add.append(instance_container)

                        machine_id = instance_container.getMetaDataEntry("machine", None)
                        if machine_id:
                            new_machine_id = self.getNewId(machine_id)
                            new_id = new_machine_id + "_current_settings"
                            instance_container._id = new_id
                            instance_container.setName(new_id)
                            instance_container.setMetaDataEntry("machine", new_machine_id)
                            containers_to_add.append(instance_container)
                user_instance_containers.append(instance_container)
            elif container_type in ("quality_changes", "definition_changes"):
                # Check if quality changes already exists.
                changes_containers = self._container_registry.findInstanceContainers(id = container_id)
                if not changes_containers:
                    # no existing containers with the same ID, so we can safely add the new one
                    containers_to_add.append(instance_container)
                else:
                    # we have found existing container with the same ID, so we need to resolve according to the
                    # selected strategy.
                    if self._resolve_strategies[container_type] == "override":
                        instance_container = changes_containers[0]
                        instance_container.deserialize(archive.open(instance_container_file).read().decode("utf-8"))
                        instance_container.setDirty(True)

                    elif self._resolve_strategies[container_type] == "new":
                        # TODO: how should we handle the case "new" for quality_changes and definition_changes?

                        instance_container.setName(self._container_registry.uniqueName(instance_container.getName()))
                        new_changes_container_id = self.getNewId(instance_container.getId())
                        instance_container._id = new_changes_container_id

                        # TODO: we don't know the following is correct or not, need to verify
                        #       AND REFACTOR!!!
                        if self._resolve_strategies["machine"] == "new":
                            # The machine is going to get a spiffy new name, so ensure that the id's of user settings match.
                            old_extruder_id = instance_container.getMetaDataEntry("extruder", None)
                            if old_extruder_id:
                                new_extruder_id = extruder_stack_id_map[old_extruder_id]
                                instance_container.setMetaDataEntry("extruder", new_extruder_id)

                            machine_id = instance_container.getMetaDataEntry("machine", None)
                            if machine_id:
                                new_machine_id = self.getNewId(machine_id)
                                instance_container.setMetaDataEntry("machine", new_machine_id)

                        containers_to_add.append(instance_container)

                    elif self._resolve_strategies[container_type] is None:
                        # The ID already exists, but nothing in the values changed, so do nothing.
                        pass
                quality_and_definition_changes_instance_containers.append(instance_container)
            else:
                existing_container = self._container_registry.findInstanceContainers(id = container_id)
                if not existing_container:
                    containers_to_add.append(instance_container)
            if global_stack_need_rename:
                if instance_container.getMetaDataEntry("machine"):
                    instance_container.setMetaDataEntry("machine", global_stack_id_new)

        # Add all the containers right before we try to add / serialize the stack
        for container in containers_to_add:
            self._container_registry.addContainer(container)
            container.setDirty(True)
            containers_added.append(container)

        # Get the stack(s) saved in the workspace.
        Logger.log("d", "Workspace loading is checking stacks containers...")

        # --
        # load global stack file
        try:
            # Check if a stack by this ID already exists;
            container_stacks = self._container_registry.findContainerStacks(id = global_stack_id_original)
            if container_stacks:
                stack = container_stacks[0]

                if self._resolve_strategies["machine"] == "override":
                    # TODO: HACK
                    # There is a machine, check if it has authentication data. If so, keep that data.
                    network_authentication_id = container_stacks[0].getMetaDataEntry("network_authentication_id")
                    network_authentication_key = container_stacks[0].getMetaDataEntry("network_authentication_key")
                    container_stacks[0].deserialize(archive.open(global_stack_file).read().decode("utf-8"))
                    if network_authentication_id:
                        container_stacks[0].addMetaDataEntry("network_authentication_id", network_authentication_id)
                    if network_authentication_key:
                        container_stacks[0].addMetaDataEntry("network_authentication_key", network_authentication_key)
                elif self._resolve_strategies["machine"] == "new":
                    stack = GlobalStack(global_stack_id_new)
                    stack.deserialize(archive.open(global_stack_file).read().decode("utf-8"))

                    # Ensure a unique ID and name
                    stack._id = global_stack_id_new

                    # Extruder stacks are "bound" to a machine. If we add the machine as a new one, the id of the
                    # bound machine also needs to change.
                    if stack.getMetaDataEntry("machine", None):
                        stack.setMetaDataEntry("machine", global_stack_id_new)

                    # Only machines need a new name, stacks may be non-unique
                    stack.setName(self._container_registry.uniqueName(stack.getName()))
                    container_stacks_added.append(stack)
                    self._container_registry.addContainer(stack)
                else:
                    Logger.log("w", "Resolve strategy of %s for machine is not supported", self._resolve_strategies["machine"])
            else:
                # no existing container stack, so we create a new one
                stack = GlobalStack(global_stack_id_new)
                # Deserialize stack by converting read data from bytes to string
                stack.deserialize(archive.open(global_stack_file).read().decode("utf-8"))
                container_stacks_added.append(stack)
                self._container_registry.addContainer(stack)
                containers_added.append(stack)

            global_stack = stack
            Job.yieldThread()
        except:
            Logger.logException("w", "We failed to serialize the stack. Trying to clean up.")
            # Something went really wrong. Try to remove any data that we added.
            for container in containers_added:
                self._container_registry.removeContainer(container.getId())
            return

        # --
        # load extruder stack files
        try:
            for index, extruder_stack_file in enumerate(extruder_stack_files):
                container_id = self._stripFileToId(extruder_stack_file)
                extruder_file_content = archive.open(extruder_stack_file, "r").read().decode("utf-8")

                container_stacks = self._container_registry.findContainerStacks(id = container_id)
                if container_stacks:
                    # this container stack already exists, try to resolve
                    stack = container_stacks[0]

                    if self._resolve_strategies["machine"] == "override":
                        # NOTE: This is the same code as those in the lower part
                        # deserialize new extruder stack over the current ones
                        stack = self._overrideExtruderStack(global_stack, index, extruder_file_content)

                    elif self._resolve_strategies["machine"] == "new":
                        # create a new extruder stack from this one
                        new_id = extruder_stack_id_map[container_id]
                        stack = ExtruderStack(new_id)

                        # HACK: the global stack can have a new name, so we need to make sure that this extruder stack
                        #       references to the new name instead of the old one. Normally, this can be done after
                        #       deserialize() by setting the metadata, but in the case of ExtruderStack, deserialize()
                        #       also does addExtruder() to its machine stack, so we have to make sure that it's pointing
                        #       to the right machine BEFORE deserialization.
                        extruder_config = configparser.ConfigParser()
                        extruder_config.read_string(extruder_file_content)
                        extruder_config.set("metadata", "machine", global_stack_id_new)
                        tmp_string_io = io.StringIO()
                        extruder_config.write(tmp_string_io)
                        extruder_file_content = tmp_string_io.getvalue()

                        stack.deserialize(extruder_file_content)

                        # Ensure a unique ID and name
                        stack._id = new_id

                        self._container_registry.addContainer(stack)
                        extruder_stacks_added.append(stack)
                        containers_added.append(stack)
                else:
                    # No extruder stack with the same ID can be found
                    if self._resolve_strategies["machine"] == "override":
                        # deserialize new extruder stack over the current ones
                        stack = self._overrideExtruderStack(global_stack, index, extruder_file_content)

                    elif self._resolve_strategies["machine"] == "new":
                        # container not found, create a new one
                        stack = ExtruderStack(container_id)

                        # HACK: the global stack can have a new name, so we need to make sure that this extruder stack
                        #       references to the new name instead of the old one. Normally, this can be done after
                        #       deserialize() by setting the metadata, but in the case of ExtruderStack, deserialize()
                        #       also does addExtruder() to its machine stack, so we have to make sure that it's pointing
                        #       to the right machine BEFORE deserialization.
                        extruder_config = configparser.ConfigParser()
                        extruder_config.read_string(extruder_file_content)
                        extruder_config.set("metadata", "machine", global_stack_id_new)
                        tmp_string_io = io.StringIO()
                        extruder_config.write(tmp_string_io)
                        extruder_file_content = tmp_string_io.getvalue()

                        stack.deserialize(extruder_file_content)
                        self._container_registry.addContainer(stack)
                        extruder_stacks_added.append(stack)
                        containers_added.append(stack)
                    else:
                        Logger.log("w", "Unknown resolve strategy: %s" % str(self._resolve_strategies["machine"]))

                extruder_stacks.append(stack)
        except:
            Logger.logException("w", "We failed to serialize the stack. Trying to clean up.")
            # Something went really wrong. Try to remove any data that we added. 
            for container in containers_added:
                self._container_registry.removeContainer(container.getId())
            return

        #
        # Replacing the old containers if resolve is "new".
        # When resolve is "new", some containers will get renamed, so all the other containers that reference to those
        # MUST get updated too.
        #
        if self._resolve_strategies["machine"] == "new":
            # A new machine was made, but it was serialized with the wrong user container. Fix that now.
            for container in user_instance_containers:
                # replacing the container ID for user instance containers for the extruders
                extruder_id = container.getMetaDataEntry("extruder", None)
                if extruder_id:
                    for extruder in extruder_stacks:
                        if extruder.getId() == extruder_id:
                            extruder.userChanges = container
                            continue

                # replacing the container ID for user instance containers for the machine
                machine_id = container.getMetaDataEntry("machine", None)
                if machine_id:
                    if global_stack.getId() == machine_id:
                        global_stack.userChanges = container
                        continue

        for changes_container_type in ("quality_changes", "definition_changes"):
            if self._resolve_strategies[changes_container_type] == "new":
                # Quality changes needs to get a new ID, added to registry and to the right stacks
                for each_changes_container in quality_and_definition_changes_instance_containers:
                    # NOTE: The renaming and giving new IDs are possibly redundant because they are done in the
                    #       instance container loading part.
                    new_id = each_changes_container.getId()

                    # Find the old (current) changes container in the global stack
                    if changes_container_type == "quality_changes":
                        old_container = global_stack.qualityChanges
                    elif changes_container_type == "definition_changes":
                        old_container = global_stack.definitionChanges

                    # sanity checks
                    # NOTE: The following cases SHOULD NOT happen!!!!
                    if not old_container:
                        Logger.log("e", "We try to get [%s] from the global stack [%s] but we got None instead!",
                                   changes_container_type, global_stack.getId())

                    # Replace the quality/definition changes container if it's in the GlobalStack
                    # NOTE: we can get an empty container here, but the IDs will not match,
                    # so this comparison is fine.
                    if self._id_mapping.get(old_container.getId()) == new_id:
                        if changes_container_type == "quality_changes":
                            global_stack.qualityChanges = each_changes_container
                        elif changes_container_type == "definition_changes":
                            global_stack.definitionChanges = each_changes_container
                        continue

                    # Replace the quality/definition changes container if it's in one of the ExtruderStacks
                    for each_extruder_stack in extruder_stacks:
                        changes_container = None
                        if changes_container_type == "quality_changes":
                            changes_container = each_extruder_stack.qualityChanges
                        elif changes_container_type == "definition_changes":
                            changes_container = each_extruder_stack.definitionChanges

                        # sanity checks
                        # NOTE: The following cases SHOULD NOT happen!!!!
                        if not changes_container:
                            Logger.log("e", "We try to get [%s] from the extruder stack [%s] but we got None instead!",
                                       changes_container_type, each_extruder_stack.getId())

                        # NOTE: we can get an empty container here, but the IDs will not match,
                        # so this comparison is fine.
                        if self._id_mapping.get(changes_container.getId()) == new_id:
                            if changes_container_type == "quality_changes":
                                each_extruder_stack.qualityChanges = each_changes_container
                            elif changes_container_type == "definition_changes":
                                each_extruder_stack.definitionChanges = each_changes_container

        if self._resolve_strategies["material"] == "new":
            for each_material in material_containers:
                old_material = global_stack.material

                # check if the old material container has been renamed to this material container ID
                # if the container hasn't been renamed, we do nothing.
                new_id = self._id_mapping.get(old_material.getId())
                if new_id is None or new_id != each_material.getId():
                    continue

                if old_material.getId() in self._id_mapping:
                    global_stack.material = each_material

                for each_extruder_stack in extruder_stacks:
                    old_material = each_extruder_stack.material

                    # check if the old material container has been renamed to this material container ID
                    # if the container hasn't been renamed, we do nothing.
                    new_id = self._id_mapping.get(old_material.getId())
                    if new_id is None or new_id != each_material.getId():
                        continue

                    if old_material.getId() in self._id_mapping:
                        each_extruder_stack.material = each_material

        if extruder_stacks:
            for stack in extruder_stacks:
                ExtruderManager.getInstance().registerExtruder(stack, global_stack.getId())
        else:
            # Machine has no extruders, but it needs to be registered with the extruder manager.
            ExtruderManager.getInstance().registerExtruder(None, global_stack.getId())

        Logger.log("d", "Workspace loading is notifying rest of the code of changes...")

        if self._resolve_strategies["machine"] == "new":
            for stack in extruder_stacks:
                stack.setNextStack(global_stack)
                stack.containersChanged.emit(stack.getTop())

        # Actually change the active machine.
        Application.getInstance().setGlobalContainerStack(global_stack)

        # Notify everything/one that is to notify about changes.
        global_stack.containersChanged.emit(global_stack.getTop())

        # Load all the nodes / meshdata of the workspace
        nodes = self._3mf_mesh_reader.read(file_name)
        if nodes is None:
            nodes = []
        return nodes

    def _stripFileToId(self, file):
        mime_type = MimeTypeDatabase.getMimeTypeForFile(file)
        file = mime_type.stripExtension(file)
        return file.replace("Cura/", "")

    def _getXmlProfileClass(self):
        return self._container_registry.getContainerForMimeType(MimeTypeDatabase.getMimeType("application/x-ultimaker-material-profile"))

    ##  Get the list of ID's of all containers in a container stack by partially parsing it's serialized data.
    def _getContainerIdListFromSerialized(self, serialized):
        parser = configparser.ConfigParser(interpolation=None, empty_lines_in_values=False)
        parser.read_string(serialized)

        container_ids = []
        if "containers" in parser:
            for index, container_id in parser.items("containers"):
                container_ids.append(container_id)
        elif parser.has_option("general", "containers"):
            container_string = parser["general"].get("containers", "")
            container_list = container_string.split(",")
            container_ids = [container_id for container_id in container_list if container_id != ""]

        return container_ids

    def _getMachineNameFromSerializedStack(self, serialized):
        parser = configparser.ConfigParser(interpolation=None, empty_lines_in_values=False)
        parser.read_string(serialized)
        return parser["general"].get("name", "")

    def _getMaterialLabelFromSerialized(self, serialized):
        data = ET.fromstring(serialized)
        metadata = data.iterfind("./um:metadata/um:name/um:label", {"um": "http://www.ultimaker.com/material"})
        for entry in metadata:
            return entry.text
        pass

