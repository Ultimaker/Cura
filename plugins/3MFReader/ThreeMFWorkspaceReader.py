from UM.Workspace.WorkspaceReader import WorkspaceReader
from UM.Application import Application

from UM.Logger import Logger
from UM.i18n import i18nCatalog
from UM.Settings.ContainerStack import ContainerStack
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.ContainerRegistry import ContainerRegistry

from UM.Preferences import Preferences
from .WorkspaceDialog import WorkspaceDialog

from cura.Settings.ExtruderManager import ExtruderManager

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
        self._definition_container_suffix = ContainerRegistry.getMimeTypeForContainer(DefinitionContainer).suffixes[0]
        self._material_container_suffix = None # We have to wait until all other plugins are loaded before we can set it
        self._instance_container_suffix = ContainerRegistry.getMimeTypeForContainer(InstanceContainer).suffixes[0]
        self._container_stack_suffix = ContainerRegistry.getMimeTypeForContainer(ContainerStack).suffixes[0]

        self._resolve_strategies = {}

        self._id_mapping = {}

    ##  Get a unique name based on the old_id. This is different from directly calling the registry in that it caches results.
    #   This has nothing to do with speed, but with getting consistent new naming for instances & objects.
    def getNewId(self, old_id):
        if old_id not in self._id_mapping:
            self._id_mapping[old_id] = self._container_registry.uniqueName(old_id)
        return self._id_mapping[old_id]

    def preRead(self, file_name):
        self._3mf_mesh_reader = Application.getInstance().getMeshFileHandler().getReaderForFile(file_name)
        if self._3mf_mesh_reader and self._3mf_mesh_reader.preRead(file_name) == WorkspaceReader.PreReadResult.accepted:
            pass
        else:
            Logger.log("w", "Could not find reader that was able to read the scene data for 3MF workspace")
            return WorkspaceReader.PreReadResult.failed

        # Check if there are any conflicts, so we can ask the user.
        archive = zipfile.ZipFile(file_name, "r")
        cura_file_names = [name for name in archive.namelist() if name.startswith("Cura/")]
        container_stack_files = [name for name in cura_file_names if name.endswith(self._container_stack_suffix)]
        self._resolve_strategies = {"machine": None, "quality_changes": None}
        machine_conflict = False
        quality_changes_conflict = False
        for container_stack_file in container_stack_files:
            container_id = self._stripFileToId(container_stack_file)
            stacks = self._container_registry.findContainerStacks(id=container_id)
            if stacks:
                # Check if there are any changes at all in any of the container stacks.
                id_list = self._getContainerIdListFromSerialized(archive.open(container_stack_file).read().decode("utf-8"))
                for index, container_id in enumerate(id_list):
                    if stacks[0].getContainer(index).getId() != container_id:
                        machine_conflict = True
                        break

        material_conflict = False
        xml_material_profile = self._getXmlProfileClass()
        if self._material_container_suffix is None:
            self._material_container_suffix = ContainerRegistry.getMimeTypeForContainer(xml_material_profile).suffixes[0]
        if xml_material_profile:
            material_container_files = [name for name in cura_file_names if name.endswith(self._material_container_suffix)]
            for material_container_file in material_container_files:
                container_id = self._stripFileToId(material_container_file)
                materials = self._container_registry.findInstanceContainers(id=container_id)
                if materials and not materials[0].isReadOnly():  # Only non readonly materials can be in conflict
                    material_conflict = True

        # Check if any quality_changes instance container is in conflict.
        instance_container_files = [name for name in cura_file_names if name.endswith(self._instance_container_suffix)]
        for instance_container_file in instance_container_files:
            container_id = self._stripFileToId(instance_container_file)
            instance_container = InstanceContainer(container_id)

            # Deserialize InstanceContainer by converting read data from bytes to string
            instance_container.deserialize(archive.open(instance_container_file).read().decode("utf-8"))
            container_type = instance_container.getMetaDataEntry("type")
            if container_type == "quality_changes":
                # Check if quality changes already exists.
                quality_changes = self._container_registry.findInstanceContainers(id = container_id)
                if quality_changes:
                    # Check if there really is a conflict by comparing the values
                    if quality_changes[0] != instance_container:
                        quality_changes_conflict = True
                        break
        try:
            archive.open("Cura/preferences.cfg")
        except KeyError:
            # If there is no preferences file, it's not a workspace, so notify user of failure.
            Logger.log("w", "File %s is not a valid workspace.", file_name)
            return WorkspaceReader.PreReadResult.failed

        if machine_conflict or quality_changes_conflict or material_conflict:
            # There is a conflict; User should choose to either update the existing data, add everything as new data or abort
            self._dialog.setMachineConflict(machine_conflict)
            self._dialog.setQualityChangesConflict(quality_changes_conflict)
            self._dialog.setMaterialConflict(material_conflict)
            self._dialog.show()
            self._dialog.waitForClose()
            if self._dialog.getResult() == {}:
                return WorkspaceReader.PreReadResult.cancelled

            self._resolve_strategies = self._dialog.getResult()

        return WorkspaceReader.PreReadResult.accepted

    def read(self, file_name):
        # Load all the nodes / meshdata of the workspace
        nodes = self._3mf_mesh_reader.read(file_name)
        if nodes is None:
            nodes = []

        archive = zipfile.ZipFile(file_name, "r")

        cura_file_names = [name for name in archive.namelist() if name.startswith("Cura/")]

        # Create a shadow copy of the preferences (we don't want all of the preferences, but we do want to re-use its
        # parsing code.
        temp_preferences = Preferences()
        temp_preferences.readFromFile(io.TextIOWrapper(archive.open("Cura/preferences.cfg")))  # We need to wrap it, else the archive parser breaks.

        # Copy a number of settings from the temp preferences to the global
        global_preferences = Preferences.getInstance()
        global_preferences.setValue("general/visible_settings", temp_preferences.getValue("general/visible_settings"))
        global_preferences.setValue("cura/categories_expanded", temp_preferences.getValue("cura/categories_expanded"))
        Application.getInstance().expandedCategoriesChanged.emit()  # Notify the GUI of the change

        self._id_mapping = {}

        # TODO: For the moment we use pretty naive existence checking. If the ID is the same, we assume in quite a few
        # TODO: cases that the container loaded is the same (most notable in materials & definitions).
        # TODO: It might be possible that we need to add smarter checking in the future.
        Logger.log("d", "Workspace loading is checking definitions...")
        # Get all the definition files & check if they exist. If not, add them.
        definition_container_files = [name for name in cura_file_names if name.endswith(self._definition_container_suffix)]
        for definition_container_file in definition_container_files:
            container_id = self._stripFileToId(definition_container_file)
            definitions = self._container_registry.findDefinitionContainers(id=container_id)
            if not definitions:
                definition_container = DefinitionContainer(container_id)
                definition_container.deserialize(archive.open(definition_container_file).read().decode("utf-8"))
                self._container_registry.addContainer(definition_container)

        Logger.log("d", "Workspace loading is checking materials...")
        # Get all the material files and check if they exist. If not, add them.
        xml_material_profile = self._getXmlProfileClass()
        if self._material_container_suffix is None:
            self._material_container_suffix = ContainerRegistry.getMimeTypeForContainer(xml_material_profile).suffixes[0]
        if xml_material_profile:
            material_container_files = [name for name in cura_file_names if name.endswith(self._material_container_suffix)]
            for material_container_file in material_container_files:
                container_id = self._stripFileToId(material_container_file)
                materials = self._container_registry.findInstanceContainers(id=container_id)
                if not materials:
                    material_container = xml_material_profile(container_id)
                    material_container.deserialize(archive.open(material_container_file).read().decode("utf-8"))
                    self._container_registry.addContainer(material_container)
                else:
                    pass


        Logger.log("d", "Workspace loading is checking instance containers...")
        # Get quality_changes and user profiles saved in the workspace
        instance_container_files = [name for name in cura_file_names if name.endswith(self._instance_container_suffix)]
        user_instance_containers = []
        quality_changes_instance_containers = []
        for instance_container_file in instance_container_files:
            container_id = self._stripFileToId(instance_container_file)
            instance_container = InstanceContainer(container_id)

            # Deserialize InstanceContainer by converting read data from bytes to string
            instance_container.deserialize(archive.open(instance_container_file).read().decode("utf-8"))
            container_type = instance_container.getMetaDataEntry("type")
            if container_type == "user":
                # Check if quality changes already exists.
                user_containers = self._container_registry.findInstanceContainers(id=container_id)
                if not user_containers:
                    self._container_registry.addContainer(instance_container)
                else:
                    if self._resolve_strategies["machine"] == "override":
                        user_containers[0].deserialize(archive.open(instance_container_file).read().decode("utf-8"))
                    elif self._resolve_strategies["machine"] == "new":
                        # The machine is going to get a spiffy new name, so ensure that the id's of user settings match.
                        extruder_id = instance_container.getMetaDataEntry("extruder", None)
                        if extruder_id:
                            new_id = self.getNewId(extruder_id) + "_current_settings"
                            instance_container._id = new_id
                            instance_container.setName(new_id)
                            instance_container.setMetaDataEntry("extruder", self.getNewId(extruder_id))
                            self._container_registry.addContainer(instance_container)

                        machine_id = instance_container.getMetaDataEntry("machine", None)
                        if machine_id:
                            new_id = self.getNewId(machine_id) + "_current_settings"
                            instance_container._id = new_id
                            instance_container.setName(new_id)
                            instance_container.setMetaDataEntry("machine", self.getNewId(machine_id))
                            self._container_registry.addContainer(instance_container)
                user_instance_containers.append(instance_container)
            elif container_type == "quality_changes":
                # Check if quality changes already exists.
                quality_changes = self._container_registry.findInstanceContainers(id = container_id)
                if not quality_changes:
                    self._container_registry.addContainer(instance_container)
                else:
                    if self._resolve_strategies["quality_changes"] == "override":
                        quality_changes[0].deserialize(archive.open(instance_container_file).read().decode("utf-8"))
                    elif self._resolve_strategies["quality_changes"] is None:
                        # The ID already exists, but nothing in the values changed, so do nothing.
                        pass
                quality_changes_instance_containers.append(instance_container)
            else:
                continue

        # Get the stack(s) saved in the workspace.
        Logger.log("d", "Workspace loading is checking stacks containers...")
        container_stack_files = [name for name in cura_file_names if name.endswith(self._container_stack_suffix)]
        global_stack = None
        extruder_stacks = []
        for container_stack_file in container_stack_files:
            container_id = self._stripFileToId(container_stack_file)

            # Check if a stack by this ID already exists;
            container_stacks = self._container_registry.findContainerStacks(id=container_id)
            if container_stacks:
                stack = container_stacks[0]
                if self._resolve_strategies["machine"] == "override":
                    container_stacks[0].deserialize(archive.open(container_stack_file).read().decode("utf-8"))
                elif self._resolve_strategies["machine"] == "new":
                    new_id = self.getNewId(container_id)
                    stack = ContainerStack(new_id)
                    stack.deserialize(archive.open(container_stack_file).read().decode("utf-8"))

                    # Ensure a unique ID and name
                    stack._id = new_id

                    # Extruder stacks are "bound" to a machine. If we add the machine as a new one, the id of the
                    # bound machine also needs to change.
                    if stack.getMetaDataEntry("machine", None):
                        stack.setMetaDataEntry("machine", self.getNewId(stack.getMetaDataEntry("machine")))

                    if stack.getMetaDataEntry("type") != "extruder_train":
                        # Only machines need a new name, stacks may be non-unique
                        stack.setName(self._container_registry.uniqueName(stack.getName()))
                    self._container_registry.addContainer(stack)
                else:
                    Logger.log("w", "Resolve strategy of %s for machine is not supported", self._resolve_strategies["machine"])
            else:
                stack = ContainerStack(container_id)
                # Deserialize stack by converting read data from bytes to string
                stack.deserialize(archive.open(container_stack_file).read().decode("utf-8"))
                self._container_registry.addContainer(stack)

            if stack.getMetaDataEntry("type") == "extruder_train":
                extruder_stacks.append(stack)
            else:
                global_stack = stack

        if self._resolve_strategies["machine"] == "new":
            # A new machine was made, but it was serialized with the wrong user container. Fix that now.
            for container in user_instance_containers:
                extruder_id = container.getMetaDataEntry("extruder", None)
                if extruder_id:
                    for extruder in extruder_stacks:
                        if extruder.getId() == extruder_id:
                            extruder.replaceContainer(0, container)
                            continue
                machine_id = container.getMetaDataEntry("machine", None)
                if machine_id:
                    if global_stack.getId() == machine_id:
                        global_stack.replaceContainer(0, container)
                        continue

        if self._resolve_strategies["quality_changes"] == "new":
            # Quality changes needs to get a new ID, added to registry and to the right stacks
            for container in quality_changes_instance_containers:
                old_id = container.getId()
                container.setName(self._container_registry.uniqueName(container.getName()))
                # We're not really supposed to change the ID in normal cases, but this is an exception.
                container._id = self.getNewId(container.getId())

                # The container was not added yet, as it didn't have an unique ID. It does now, so add it.
                self._container_registry.addContainer(container)

                # Replace the quality changes container
                old_container = global_stack.findContainer({"type": "quality_changes"})
                if old_container.getId() == old_id:
                    quality_changes_index = global_stack.getContainerIndex(old_container)
                    global_stack.replaceContainer(quality_changes_index, container)
                    continue

                for stack in extruder_stacks:
                    old_container = stack.findContainer({"type": "quality_changes"})
                    if old_container.getId() == old_id:
                        quality_changes_index = stack.getContainerIndex(old_container)
                        stack.replaceContainer(quality_changes_index, container)

        for stack in extruder_stacks:
            ExtruderManager.getInstance().registerExtruder(stack, global_stack.getId())
        else:
            # Machine has no extruders, but it needs to be registered with the extruder manager.
            ExtruderManager.getInstance().registerExtruder(None, global_stack.getId())

        Logger.log("d", "Workspace loading is notifying rest of the code of changes...")
        # Notify everything/one that is to notify about changes.
        for container in global_stack.getContainers():
            global_stack.containersChanged.emit(container)

        for stack in extruder_stacks:
            stack.setNextStack(global_stack)
            for container in stack.getContainers():
                stack.containersChanged.emit(container)

        # Actually change the active machine.
        Application.getInstance().setGlobalContainerStack(global_stack)
        return nodes

    def _stripFileToId(self, file):
        return file.replace("Cura/", "").split(".")[0]

    def _getXmlProfileClass(self):
        for type_name, container_type in self._container_registry.getContainerTypes():
            if type_name == "XmlMaterialProfile":
                return container_type

    ##  Get the list of ID's of all containers in a container stack by partially parsing it's serialized data.
    def _getContainerIdListFromSerialized(self, serialized):
        parser = configparser.ConfigParser(interpolation=None, empty_lines_in_values=False)
        parser.read_string(serialized)
        container_string = parser["general"].get("containers", "")
        container_list = container_string.split(",")
        return [container_id for container_id in container_list if container_id != ""]
