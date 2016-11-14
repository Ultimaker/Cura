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
import zipfile
import io

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

        self._resolve_strategy = None

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

        conflict = False
        for container_stack_file in container_stack_files:
            container_id = self._stripFileToId(container_stack_file)
            stacks = self._container_registry.findContainerStacks(id=container_id)
            if stacks:
                conflict = True
                break

        # Check if any quality_changes instance container is in conflict.
        if not conflict:
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
                        conflict = True
        if conflict:
            # There is a conflict; User should choose to either update the existing data, add everything as new data or abort
            self._resolve_strategy = None
            self._dialog.show()
            self._dialog.waitForClose()
            if self._dialog.getResult() == "cancel":
                return WorkspaceReader.PreReadResult.cancelled

            self._resolve_strategy = self._dialog.getResult()
            pass
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

        # TODO: For the moment we use pretty naive existence checking. If the ID is the same, we assume in quite a few
        # TODO: cases that the container loaded is the same (most notable in materials & definitions).
        # TODO: It might be possible that we need to add smarter checking in the future.

        # Get all the definition files & check if they exist. If not, add them.
        definition_container_files = [name for name in cura_file_names if name.endswith(self._definition_container_suffix)]
        for definition_container_file in definition_container_files:
            container_id = self._stripFileToId(definition_container_file)
            definitions = self._container_registry.findDefinitionContainers(id=container_id)
            if not definitions:
                definition_container = DefinitionContainer(container_id)
                definition_container.deserialize(archive.open(definition_container_file).read().decode("utf-8"))
                self._container_registry.addContainer(definition_container)

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
                    if self._resolve_strategy == "override":
                        user_containers[0].deserialize(archive.open(instance_container_file).read().decode("utf-8"))
                user_instance_containers.append(instance_container)
            elif container_type == "quality_changes":
                # Check if quality changes already exists.
                quality_changes = self._container_registry.findInstanceContainers(id = container_id)
                if not quality_changes:
                    self._container_registry.addContainer(instance_container)
                else:
                    if self._resolve_strategy == "override":
                        quality_changes[0].deserialize(archive.open(instance_container_file).read().decode("utf-8"))
                quality_changes_instance_containers.append(instance_container)
            else:
                continue

        # Get the stack(s) saved in the workspace.
        container_stack_files = [name for name in cura_file_names if name.endswith(self._container_stack_suffix)]
        global_stack = None
        extruder_stacks = []

        for container_stack_file in container_stack_files:
            container_id = self._stripFileToId(container_stack_file)

            stack = ContainerStack(container_id)
            # Check if a stack by this ID already exists;
            container_stacks = self._container_registry.findContainerStacks(id=container_id)
            if container_stacks:
                if self._resolve_strategy == "override":
                    container_stacks[0].deserialize(archive.open(container_stack_file).read().decode("utf-8"))
            else:
                # Deserialize stack by converting read data from bytes to string
                stack.deserialize(archive.open(container_stack_file).read().decode("utf-8"))
                self._container_registry.addContainer(stack)

            if stack.getMetaDataEntry("type") == "extruder_train":
                extruder_stacks.append(stack)
            else:
                global_stack = stack

        return nodes

    def _stripFileToId(self, file):
        return file.replace("Cura/", "").split(".")[0]

    def _getXmlProfileClass(self):
        for type_name, container_type in self._container_registry.getContainerTypes():
            print(type_name, container_type)
            if type_name == "XmlMaterialProfile":
                return container_type
