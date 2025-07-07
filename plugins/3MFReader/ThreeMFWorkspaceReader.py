# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from configparser import ConfigParser
import zipfile
import os
import json
import re
from typing import cast, Dict, List, Optional, Tuple, Any, Set

import xml.etree.ElementTree as ET

from UM.Math.AxisAlignedBox import AxisAlignedBox
from UM.Math.Vector import Vector
from UM.Util import parseBool
from UM.Workspace.WorkspaceReader import WorkspaceReader
from UM.Application import Application

from UM.Logger import Logger
from UM.Message import Message
from UM.i18n import i18nCatalog
from UM.Settings.ContainerFormatError import ContainerFormatError
from UM.Settings.ContainerStack import ContainerStack
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.MimeTypeDatabase import MimeTypeDatabase, MimeType
from UM.Job import Job
from UM.Preferences import Preferences
from cura.CuraPackageManager import CuraPackageManager

from cura.Machines.ContainerTree import ContainerTree
from cura.Settings.CuraStackBuilder import CuraStackBuilder
from cura.Settings.ExtruderManager import ExtruderManager
from cura.Settings.ExtruderStack import ExtruderStack
from cura.Settings.GlobalStack import GlobalStack
from cura.Settings.IntentManager import IntentManager
from cura.Settings.CuraContainerStack import _ContainerIndexes
from cura.CuraApplication import CuraApplication
from cura.Utils.Threading import call_on_qt_thread

from PyQt6.QtCore import QCoreApplication

from .WorkspaceDialog import WorkspaceDialog

i18n_catalog = i18nCatalog("cura")


_ignored_machine_network_metadata: Set[str] = {
    "um_cloud_cluster_id",
    "um_network_key",
    "um_linked_to_account",
    "host_guid",
    "removal_warning",
    "group_name",
    "group_size",
    "connection_type",
    "capabilities",
    "octoprint_api_key",
    "is_abstract_machine"
}

USER_SETTINGS_PATH = "Cura/user-settings.json"

class ContainerInfo:
    def __init__(self, file_name: Optional[str], serialized: Optional[str], parser: Optional[ConfigParser]) -> None:
        self.file_name = file_name
        self.serialized = serialized
        self.parser = parser
        self.container = None
        self.definition_id = None


class QualityChangesInfo:
    def __init__(self) -> None:
        self.name: Optional[str] = None
        self.global_info = None
        self.extruder_info_dict: Dict[str, ContainerInfo] = {}


class MachineInfo:
    def __init__(self) -> None:
        self.container_id: Optional[str] = None
        self.name: Optional[str] = None
        self.definition_id: Optional[str] = None

        self.metadata_dict: Dict[str, str] = {}

        self.quality_type: Optional[str] = None
        self.intent_category: Optional[str] = None
        self.custom_quality_name: Optional[str] = None
        self.quality_changes_info: Optional[QualityChangesInfo] = None
        self.variant_info: Optional[ContainerInfo] = None

        self.definition_changes_info: Optional[ContainerInfo] = None
        self.user_changes_info: Optional[ContainerInfo] = None

        self.extruder_info_dict: Dict[str, str] = {}


class ExtruderInfo:
    def __init__(self) -> None:
        self.position = None
        self.enabled = True
        self.variant_info: Optional[ContainerInfo] = None
        self.root_material_id: Optional[str] = None

        self.definition_changes_info: Optional[ContainerInfo] = None
        self.user_changes_info: Optional[ContainerInfo] = None
        self.intent_info: Optional[ContainerInfo] = None


class ThreeMFWorkspaceReader(WorkspaceReader):
    """Base implementation for reading 3MF workspace files."""

    def __init__(self) -> None:
        super().__init__()

        self._supported_extensions = [".3mf"]
        self._dialog = WorkspaceDialog()
        self._3mf_mesh_reader = None
        self._is_ucp = None
        self._container_registry = ContainerRegistry.getInstance()

        # suffixes registered with the MimeTypes don't start with a dot '.'
        self._definition_container_suffix = "." + cast(MimeType, ContainerRegistry.getMimeTypeForContainer(DefinitionContainer)).preferredSuffix
        self._material_container_suffix = None # We have to wait until all other plugins are loaded before we can set it
        self._instance_container_suffix = "." + cast(MimeType, ContainerRegistry.getMimeTypeForContainer(InstanceContainer)).preferredSuffix
        self._container_stack_suffix = "." + cast(MimeType, ContainerRegistry.getMimeTypeForContainer(ContainerStack)).preferredSuffix
        self._extruder_stack_suffix = "." + cast(MimeType, ContainerRegistry.getMimeTypeForContainer(ExtruderStack)).preferredSuffix
        self._global_stack_suffix = "." + cast(MimeType, ContainerRegistry.getMimeTypeForContainer(GlobalStack)).preferredSuffix

        # Certain instance container types are ignored because we make the assumption that only we make those types
        # of containers. They are:
        #  - quality
        #  - variant
        self._ignored_instance_container_types = {"quality", "variant"}

        self._resolve_strategies: Dict[str, str] = {}

        self._id_mapping: Dict[str, str] = {}

        # In Cura 2.5 and 2.6, the empty profiles used to have those long names
        self._old_empty_profile_id_dict = {"empty_%s" % k: "empty" for k in ["material", "variant"]}

        self._old_new_materials: Dict[str, str] = {}
        self._machine_info = None

        self._user_settings: Dict[str, Dict[str, Any]] = {}

    def _clearState(self):
        self._id_mapping = {}
        self._old_new_materials = {}
        self._machine_info = None
        self._user_settings = {}

    def clearOpenAsUcp(self):
        self._is_ucp =  None

    def getNewId(self, old_id: str):
        """Get a unique name based on the old_id. This is different from directly calling the registry in that it caches results.

        This has nothing to do with speed, but with getting consistent new naming for instances & objects.
        """
        if old_id not in self._id_mapping:
            self._id_mapping[old_id] = self._container_registry.uniqueName(old_id)
        return self._id_mapping[old_id]

    def _determineGlobalAndExtruderStackFiles(self, project_file_name: str, file_list: List[str]) -> Tuple[str, List[str]]:
        """Separates the given file list into a list of GlobalStack files and a list of ExtruderStack files.

        In old versions, extruder stack files have the same suffix as container stack files ".stack.cfg".
        """

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
            stack_config = ConfigParser(interpolation = None)
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

        if len(global_stack_file_list) > 1:
            Logger.log("e", "More than one global stack file found: [{file_list}]".format(file_list = global_stack_file_list))
            #But we can recover by just getting the first global stack file.
        if len(global_stack_file_list) == 0:
            Logger.log("e", "No global stack file found!")
            raise FileNotFoundError("No global stack file found!")

        return global_stack_file_list[0], extruder_stack_file_list

    def _isProjectUcp(self, file_name) -> bool:
        if self._is_ucp == None:
            archive = zipfile.ZipFile(file_name, "r")
            cura_file_names = [name for name in archive.namelist() if name.startswith("Cura/")]
            self._is_ucp =True if USER_SETTINGS_PATH in cura_file_names else False

    def getIsProjectUcp(self) -> bool:
        return self._is_ucp


    def preRead(self, file_name, show_dialog=True, *args, **kwargs):
        """Read some info so we can make decisions

        :param file_name:
        :param show_dialog: In case we use preRead() to check if a file is a valid project file,
                            we don't want to show a dialog.
        """
        self._clearState()
        self._isProjectUcp(file_name)
        self._3mf_mesh_reader = Application.getInstance().getMeshFileHandler().getReaderForFile(file_name)
        if self._3mf_mesh_reader and self._3mf_mesh_reader.preRead(file_name) == WorkspaceReader.PreReadResult.accepted:
            pass
        else:
            Logger.log("w", "Could not find reader that was able to read the scene data for 3MF workspace")
            return WorkspaceReader.PreReadResult.failed

        self._machine_info = MachineInfo()
        machine_type = ""
        variant_type_name = i18n_catalog.i18nc("@label", "Nozzle")

        # Check if there are any conflicts, so we can ask the user.
        archive = zipfile.ZipFile(file_name, "r")
        cura_file_names = [name for name in archive.namelist() if name.startswith("Cura/")]

        resolve_strategy_keys = ["machine", "material", "quality_changes"]
        self._resolve_strategies = {k: None for k in resolve_strategy_keys}
        containers_found_dict = {k: False for k in resolve_strategy_keys}

        # Check whether the file is a UCP, which changes some import options
        is_ucp = USER_SETTINGS_PATH in cura_file_names

        #
        # Read definition containers
        #
        machine_definition_id = None
        updatable_machines = None if self._is_ucp else []
        machine_definition_container_count = 0
        extruder_definition_container_count = 0
        definition_container_files = [name for name in cura_file_names if name.endswith(self._definition_container_suffix)]
        for definition_container_file in definition_container_files:
            container_id = self._stripFileToId(definition_container_file)
            definitions = self._container_registry.findDefinitionContainersMetadata(id = container_id)
            serialized = archive.open(definition_container_file).read().decode("utf-8")

            if not definitions:
                definition_container = DefinitionContainer.deserializeMetadata(serialized, container_id)[0]
            else:
                definition_container = definitions[0]

            definition_container_type = definition_container.get("type")
            if definition_container_type == "machine":
                machine_definition_id = container_id
                machine_definition_containers = self._container_registry.findDefinitionContainers(id = machine_definition_id)
                if machine_definition_containers and updatable_machines is not None:
                    updatable_machines = [machine for machine in self._container_registry.findContainerStacks(type = "machine") if machine.definition == machine_definition_containers[0]]
                machine_type = definition_container["name"]
                variant_type_name = definition_container.get("variants_name", variant_type_name)

                machine_definition_container_count += 1
            elif definition_container_type == "extruder":
                extruder_definition_container_count += 1
            else:
                Logger.log("w", "Unknown definition container type %s for %s",
                           definition_container_type, definition_container_file)
            QCoreApplication.processEvents()  # Ensure that the GUI does not freeze.
            Job.yieldThread()

        if machine_definition_container_count != 1:
            return WorkspaceReader.PreReadResult.failed  # Not a workspace file but ordinary 3MF.

        material_ids_to_names_map = {}
        material_conflict = False
        xml_material_profile = self._getXmlProfileClass()
        reverse_material_id_dict = {}
        if self._material_container_suffix is None:
            self._material_container_suffix = ContainerRegistry.getMimeTypeForContainer(xml_material_profile).preferredSuffix
        if xml_material_profile:
            material_container_files = [name for name in cura_file_names if name.endswith(self._material_container_suffix)]
            for material_container_file in material_container_files:
                container_id = self._stripFileToId(material_container_file)

                serialized = archive.open(material_container_file).read().decode("utf-8")
                metadata_list = xml_material_profile.deserializeMetadata(serialized, container_id)
                reverse_map = {metadata["id"]: container_id for metadata in metadata_list}
                reverse_material_id_dict.update(reverse_map)

                material_ids_to_names_map[container_id] = self._getMaterialLabelFromSerialized(serialized)
                if self._container_registry.findContainersMetadata(id = container_id): #This material already exists.
                    containers_found_dict["material"] = True
                    if not self._container_registry.isReadOnly(container_id):  # Only non readonly materials can be in conflict
                        material_conflict = True
                QCoreApplication.processEvents()  # Ensure that the GUI does not freeze.
                Job.yieldThread()

        # Check if any quality_changes instance container is in conflict.
        instance_container_files = [name for name in cura_file_names if name.endswith(self._instance_container_suffix)]
        quality_name = ""
        custom_quality_name = ""
        intent_name = ""
        intent_category = ""
        num_settings_overridden_by_quality_changes = 0 # How many settings are changed by the quality changes
        num_user_settings = 0
        quality_changes_conflict = False

        self._machine_info.quality_changes_info = QualityChangesInfo()

        quality_changes_info_list = []
        instance_container_info_dict = {}  # id -> parser
        for instance_container_file_name in instance_container_files:
            container_id = self._stripFileToId(instance_container_file_name)

            serialized = archive.open(instance_container_file_name).read().decode("utf-8")

            # Qualities and variants don't have upgrades, so don't upgrade them
            parser = ConfigParser(interpolation = None, comment_prefixes = ())
            parser.read_string(serialized)
            container_type = parser["metadata"]["type"]
            if container_type not in ("quality", "variant"):
                serialized = InstanceContainer._updateSerialized(serialized, instance_container_file_name)

            parser = ConfigParser(interpolation = None, comment_prefixes = ())
            parser.read_string(serialized)
            container_info = ContainerInfo(instance_container_file_name, serialized, parser)
            instance_container_info_dict[container_id] = container_info

            container_type = parser["metadata"]["type"]
            if container_type == "quality_changes":
                quality_changes_info_list.append(container_info)

                if not parser.has_option("metadata", "position"):
                    self._machine_info.quality_changes_info.name = parser["general"]["name"]
                    self._machine_info.quality_changes_info.global_info = container_info
                else:
                    position = parser["metadata"]["position"]
                    self._machine_info.quality_changes_info.extruder_info_dict[position] = container_info

                custom_quality_name = parser["general"]["name"]
                values = parser["values"] if parser.has_section("values") else dict()
                num_settings_overridden_by_quality_changes += len(values)
                # Check if quality changes already exists.
                quality_changes = self._container_registry.findInstanceContainers(name = custom_quality_name,
                                                                                  type = "quality_changes")
                if quality_changes:
                    containers_found_dict["quality_changes"] = True
                    # Check if there really is a conflict by comparing the values
                    instance_container = InstanceContainer(container_id)
                    try:
                        instance_container.deserialize(serialized, file_name = instance_container_file_name)
                    except ContainerFormatError:
                        Logger.logException("e", "Failed to deserialize InstanceContainer %s from project file %s",
                                            instance_container_file_name, file_name)
                        return ThreeMFWorkspaceReader.PreReadResult.failed
                    if quality_changes[0] != instance_container:
                        quality_changes_conflict = True
            elif container_type == "quality":
                if not quality_name:
                    quality_name = parser["general"]["name"]
            elif container_type == "intent":
                if not intent_name:
                    intent_name = parser["general"]["name"]
                    intent_category = parser["metadata"]["intent_category"]
            elif container_type == "user":
                num_user_settings += len(parser["values"])
            elif container_type in self._ignored_instance_container_types:
                # Ignore certain instance container types
                Logger.log("w", "Ignoring instance container [%s] with type [%s]", container_id, container_type)
                continue
            QCoreApplication.processEvents()  # Ensure that the GUI does not freeze.
            Job.yieldThread()

        if self._machine_info.quality_changes_info.global_info is None:
            self._machine_info.quality_changes_info = None

        # Load ContainerStack files and ExtruderStack files
        try:
            global_stack_file, extruder_stack_files = self._determineGlobalAndExtruderStackFiles(
                file_name, cura_file_names)
        except FileNotFoundError:
            return WorkspaceReader.PreReadResult.failed
        machine_conflict = False
        # Because there can be cases as follows:
        #  - the global stack exists but some/all of the extruder stacks DON'T exist
        #  - the global stack DOESN'T exist but some/all of the extruder stacks exist
        # To simplify this, only check if the global stack exists or not
        global_stack_id = self._stripFileToId(global_stack_file)

        serialized = archive.open(global_stack_file).read().decode("utf-8")

        serialized = GlobalStack._updateSerialized(serialized, global_stack_file)
        machine_name = self._getMachineNameFromSerializedStack(serialized)
        self._machine_info.metadata_dict = self._getMetaDataDictFromSerializedStack(serialized)

        # Check if the definition has been changed (this usually happens due to an upgrade)
        id_list = self._getContainerIdListFromSerialized(serialized)
        if id_list[7] != machine_definition_id:
            machine_definition_id = id_list[7]

        stacks = self._container_registry.findContainerStacks(name = machine_name, type = "machine")
        existing_global_stack = None
        global_stack = None

        if stacks:
            global_stack = stacks[0]
            existing_global_stack = global_stack
            containers_found_dict["machine"] = True
            # Check if there are any changes at all in any of the container stacks.
            for index, container_id in enumerate(id_list):
                # take into account the old empty container IDs
                container_id = self._old_empty_profile_id_dict.get(container_id, container_id)
                if global_stack.getContainer(index).getId() != container_id:
                    machine_conflict = True
                    break

        if updatable_machines and not containers_found_dict["machine"]:
            containers_found_dict["machine"] = True

        # Get quality type
        parser = ConfigParser(interpolation = None)
        parser.read_string(serialized)
        quality_container_id = parser["containers"][str(_ContainerIndexes.Quality)]
        quality_type = "empty_quality"
        if quality_container_id not in ("empty", "empty_quality"):
            if quality_container_id in instance_container_info_dict:
                quality_type = instance_container_info_dict[quality_container_id].parser["metadata"]["quality_type"]
            else:  # If a version upgrade changed the quality profile in the stack, we'll need to look for it in the built-in profiles instead of the workspace.
                quality_matches = ContainerRegistry.getInstance().findContainersMetadata(id = quality_container_id)
                if quality_matches:  # If there's no profile with this ID, leave it empty_quality.
                    quality_type = quality_matches[0]["quality_type"]

        # Get machine info
        serialized = archive.open(global_stack_file).read().decode("utf-8")
        serialized = GlobalStack._updateSerialized(serialized, global_stack_file)
        parser = ConfigParser(interpolation = None)
        parser.read_string(serialized)
        definition_changes_id = parser["containers"][str(_ContainerIndexes.DefinitionChanges)]
        if definition_changes_id not in ("empty", "empty_definition_changes"):
            self._machine_info.definition_changes_info = instance_container_info_dict[definition_changes_id]
        user_changes_id = parser["containers"][str(_ContainerIndexes.UserChanges)]
        if user_changes_id not in ("empty", "empty_user_changes"):
            self._machine_info.user_changes_info = instance_container_info_dict[user_changes_id]

        # Also check variant and material in case it doesn't have extruder stacks
        if not extruder_stack_files:
            position = "0"

            extruder_info = ExtruderInfo()
            extruder_info.position = position
            variant_id = parser["containers"][str(_ContainerIndexes.Variant)]
            material_id = parser["containers"][str(_ContainerIndexes.Material)]
            if variant_id not in ("empty", "empty_variant"):
                extruder_info.variant_info = instance_container_info_dict[variant_id]
            if material_id not in ("empty", "empty_material"):
                root_material_id = reverse_material_id_dict[material_id]
                extruder_info.root_material_id = root_material_id
            self._machine_info.extruder_info_dict[position] = extruder_info
        else:
            variant_id = parser["containers"][str(_ContainerIndexes.Variant)]
            if variant_id not in ("empty", "empty_variant"):
                self._machine_info.variant_info = instance_container_info_dict[variant_id]
        QCoreApplication.processEvents()  # Ensure that the GUI does not freeze.
        Job.yieldThread()

        materials_in_extruders_dict = {}  # Which material is in which extruder

        # If the global stack is found, we check if there are conflicts in the extruder stacks
        for extruder_stack_file in extruder_stack_files:
            serialized = archive.open(extruder_stack_file).read().decode("utf-8")

            not_upgraded_parser = ConfigParser(interpolation=None)
            not_upgraded_parser.read_string(serialized)

            serialized = ExtruderStack._updateSerialized(serialized, extruder_stack_file)
            parser = ConfigParser(interpolation=None)
            parser.read_string(serialized)

            # The check should be done for the extruder stack that's associated with the existing global stack,
            # and those extruder stacks may have different IDs.
            # So we check according to the positions
            position = parser["metadata"]["position"]
            variant_id = parser["containers"][str(_ContainerIndexes.Variant)]
            material_id = parser["containers"][str(_ContainerIndexes.Material)]

            extruder_info = ExtruderInfo()
            extruder_info.position = position
            if parser.has_option("metadata", "enabled"):
                extruder_info.enabled = parser["metadata"]["enabled"]
            if variant_id not in ("empty", "empty_variant"):
                if variant_id in instance_container_info_dict:
                    extruder_info.variant_info = instance_container_info_dict[variant_id]

            if material_id not in ("empty", "empty_material"):
                root_material_id = reverse_material_id_dict[material_id]
                extruder_info.root_material_id = root_material_id
                materials_in_extruders_dict[position] = material_ids_to_names_map[reverse_material_id_dict[material_id]]

            definition_changes_id = parser["containers"][str(_ContainerIndexes.DefinitionChanges)]
            if definition_changes_id not in ("empty", "empty_definition_changes"):
                extruder_info.definition_changes_info = instance_container_info_dict[definition_changes_id]

            user_changes_id = parser["containers"][str(_ContainerIndexes.UserChanges)]
            if user_changes_id not in ("empty", "empty_user_changes"):
                extruder_info.user_changes_info = instance_container_info_dict[user_changes_id]
            self._machine_info.extruder_info_dict[position] = extruder_info

            intent_container_id = parser["containers"][str(_ContainerIndexes.Intent)]

            intent_id = parser["containers"][str(_ContainerIndexes.Intent)]
            if intent_id not in ("empty", "empty_intent"):
                if intent_container_id in instance_container_info_dict:
                    extruder_info.intent_info = instance_container_info_dict[intent_id]
                else:
                    # It can happen that an intent has been renamed. In that case, we should still use the old
                    # name, since we used that to generate the instance_container_info_dict keys. 
                    extruder_info.intent_info = instance_container_info_dict[not_upgraded_parser["containers"][str(_ContainerIndexes.Intent)]]

            if not machine_conflict and containers_found_dict["machine"] and global_stack:
                if int(position) >= len(global_stack.extruderList):
                    continue

                existing_extruder_stack = global_stack.extruderList[int(position)]
                # Check if there are any changes at all in any of the container stacks.
                id_list = self._getContainerIdListFromSerialized(serialized)
                for index, container_id in enumerate(id_list):
                    # Take into account the old empty container IDs
                    container_id = self._old_empty_profile_id_dict.get(container_id, container_id)
                    if existing_extruder_stack.getContainer(index).getId() != container_id:
                        machine_conflict = True
                        break

        # Now we know which material is in which extruder. Let's use that to sort the material_labels according to
        # their extruder position
        material_labels = [material_name for pos, material_name in sorted(materials_in_extruders_dict.items())]
        machine_extruder_count = self._getMachineExtruderCount()
        if machine_extruder_count:
            material_labels = material_labels[:machine_extruder_count]

        num_visible_settings = 0
        try:
            temp_preferences = Preferences()
            serialized = archive.open("Cura/preferences.cfg").read().decode("utf-8")
            temp_preferences.deserialize(serialized)

            visible_settings_string = temp_preferences.getValue("general/visible_settings")
            has_visible_settings_string = visible_settings_string is not None
            if visible_settings_string is not None:
                num_visible_settings = len(visible_settings_string.split(";"))
            active_mode = temp_preferences.getValue("cura/active_mode")
            if not active_mode:
                active_mode = Application.getInstance().getPreferences().getValue("cura/active_mode")
        except KeyError:
            # If there is no preferences file, it's not a workspace, so notify user of failure.
            Logger.log("w", "File %s is not a valid workspace.", file_name)
            return WorkspaceReader.PreReadResult.failed

        # Check if the machine definition exists. If not, indicate failure because we do not import definition files.
        def_results = self._container_registry.findDefinitionContainersMetadata(id = machine_definition_id)
        if not def_results:
            message = Message(i18n_catalog.i18nc("@info:status Don't translate the XML tags <filename> or <message>!",
                                                 "Project file <filename>{0}</filename> contains an unknown machine type"
                                                 " <message>{1}</message>. Cannot import the machine."
                                                 " Models will be imported instead.", file_name, machine_definition_id),
                                                 title = i18n_catalog.i18nc("@info:title", "Open Project File"),
                                                 message_type = Message.MessageType.WARNING)
            message.show()

            Logger.log("i", "Could unknown machine definition %s in project file %s, cannot import it.",
                       self._machine_info.definition_id, file_name)
            return WorkspaceReader.PreReadResult.failed

        # In case we use preRead() to check if a file is a valid project file, we don't want to show a dialog.
        if not show_dialog:
            return WorkspaceReader.PreReadResult.accepted

        # prepare data for the dialog
        num_extruders = extruder_definition_container_count
        if num_extruders == 0:
            num_extruders = 1  # No extruder stacks found, which means there is one extruder

        extruders = num_extruders * [""]

        quality_name = custom_quality_name if custom_quality_name else quality_name

        self._machine_info.container_id = global_stack_id
        self._machine_info.name = machine_name
        self._machine_info.definition_id = machine_definition_id
        self._machine_info.quality_type = quality_type
        self._machine_info.custom_quality_name = quality_name
        self._machine_info.intent_category = intent_category

        is_printer_group = False
        if machine_conflict:
            group_name = existing_global_stack.getMetaDataEntry("group_name")
            if group_name is not None:
                is_printer_group = True
                machine_name = group_name

        # Getting missing required package ids
        package_metadata = self._parse_packages_metadata(archive)
        missing_package_metadata = self._filter_missing_package_metadata(package_metadata)

        # Load the user specifically exported settings
        self._dialog.exportedSettingModel.clear()
        self._dialog.setCurrentMachineName("")
        if self._is_ucp:
            try:
                self._user_settings = json.loads(archive.open("Cura/user-settings.json").read().decode("utf-8"))
                any_extruder_stack = ExtruderManager.getInstance().getExtruderStack(0)
                actual_global_stack = CuraApplication.getInstance().getGlobalContainerStack()
                self._dialog.setCurrentMachineName(actual_global_stack.id)

                for stack_name, settings in self._user_settings.items():
                    if stack_name == 'global':
                        self._dialog.exportedSettingModel.addSettingsFromStack(actual_global_stack, i18n_catalog.i18nc("@label", "Global"), settings)
                    else:
                        extruder_match = re.fullmatch('extruder_([0-9]+)', stack_name)
                        if extruder_match is not None:
                            extruder_nr = int(extruder_match.group(1))
                            self._dialog.exportedSettingModel.addSettingsFromStack(any_extruder_stack,
                                                                                   i18n_catalog.i18nc("@label",
                                                                                                      "Extruder {0}", extruder_nr + 1),
                                                                                   settings)
            except KeyError as e:
                # If there is no user settings file, it's not a UCP, so notify user of failure.
                Logger.log("w", "File %s is not a valid UCP.", file_name)
                message = Message(
                    i18n_catalog.i18nc("@info:error Don't translate the XML tags <filename> or <message>!",
                                       "Project file <filename>{0}</filename> is corrupt: <message>{1}</message>.",
                                       file_name, str(e)),
                    title=i18n_catalog.i18nc("@info:title", "Can't Open Project File"),
                    message_type=Message.MessageType.ERROR)
                message.show()
                return WorkspaceReader.PreReadResult.failed

        # Show the dialog, informing the user what is about to happen.
        self._dialog.setMachineConflict(machine_conflict)
        self._dialog.setIsPrinterGroup(is_printer_group)
        self._dialog.setQualityChangesConflict(quality_changes_conflict)
        self._dialog.setMaterialConflict(material_conflict)
        self._dialog.setHasVisibleSettingsField(has_visible_settings_string)
        self._dialog.setNumVisibleSettings(num_visible_settings)
        self._dialog.setQualityName(quality_name)
        self._dialog.setQualityType(quality_type)
        self._dialog.setIntentName(intent_category)
        self._dialog.setNumSettingsOverriddenByQualityChanges(num_settings_overridden_by_quality_changes)
        self._dialog.setNumUserSettings(num_user_settings)
        self._dialog.setActiveMode(active_mode)
        self._dialog.setUpdatableMachines(updatable_machines)
        self._dialog.setMaterialLabels(material_labels)
        self._dialog.setMachineType(machine_type)
        self._dialog.setExtruders(extruders)
        self._dialog.setVariantType(variant_type_name)
        self._dialog.setHasObjectsOnPlate(Application.getInstance().platformActivity)
        self._dialog.setMissingPackagesMetadata(missing_package_metadata)
        self._dialog.setAllowCreatemachine(not self._is_ucp)
        self._dialog.setIsUcp(self._is_ucp)
        self._dialog.show()


        # Choosing the initially selected printer in MachineSelector
        is_networked_machine = False
        is_abstract_machine = False
        if global_stack and isinstance(global_stack, GlobalStack) and not self._is_ucp:
            # The machine included in the project file exists locally already, no need to change selected printers.
            is_networked_machine = global_stack.hasNetworkedConnection()
            is_abstract_machine = parseBool(existing_global_stack.getMetaDataEntry("is_abstract_machine", False))
            self._dialog.setMachineToOverride(global_stack.getId())
            self._dialog.setResolveStrategy("machine", "override")
        elif self._dialog.updatableMachinesModel.count > 0:
            # The machine included in the project file does not exist. There is another machine of the same type.
            # This will always default to an abstract machine first.
            machine = self._dialog.updatableMachinesModel.getItem(self._dialog.currentMachinePositionIndex)
            machine_name = machine["name"]
            is_networked_machine = machine["isNetworked"]
            is_abstract_machine = machine["isAbstractMachine"]
            self._dialog.setMachineToOverride(machine["id"])
            self._dialog.setResolveStrategy("machine", "override")
        else:
            # The machine included in the project file does not exist. There are no other printers of the same type. Default to "Create New".
            machine_name = i18n_catalog.i18nc("@button", "Create new")
            is_networked_machine = False
            is_abstract_machine = False
            self._dialog.setMachineToOverride(None)
            self._dialog.setResolveStrategy("machine", "new")

        self._dialog.setIsNetworkedMachine(is_networked_machine)
        self._dialog.setIsAbstractMachine(is_abstract_machine)
        self._dialog.setMachineName(machine_name)
        self._dialog.updateCompatibleMachine()

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
        #               If there is an existing container, there is no conflict between them, and default to "override"
        #               If there is no existing container, default to "new"
        #
        # Default values
        for key, strategy in self._resolve_strategies.items():
            if key not in containers_found_dict or strategy is not None:
                continue
            self._resolve_strategies[key] = "override" if containers_found_dict[key] else "new"
        return WorkspaceReader.PreReadResult.accepted

    @call_on_qt_thread
    def read(self, file_name):
        """Read the project file

        Add all the definitions / materials / quality changes that do not exist yet. Then it loads
        all the stacks into the container registry. In some cases it will reuse the container for the global stack.
        It handles old style project files containing .stack.cfg as well as new style project files
        containing global.cfg / extruder.cfg

        :param file_name:
        """
        application = CuraApplication.getInstance()

        try:
            archive = zipfile.ZipFile(file_name, "r")
        except EnvironmentError as e:
            message = Message(i18n_catalog.i18nc("@info:error Don't translate the XML tags <filename> or <message>!",
                                                 "Project file <filename>{0}</filename> is suddenly inaccessible: <message>{1}</message>.", file_name, str(e)),
                              title = i18n_catalog.i18nc("@info:title", "Can't Open Project File"),
                              message_type = Message.MessageType.ERROR)
            message.show()
            self.setWorkspaceName("")
            return [], {}
        except zipfile.BadZipFile as e:
            message = Message(i18n_catalog.i18nc("@info:error Don't translate the XML tags <filename> or <message>!",
                                                 "Project file <filename>{0}</filename> is corrupt: <message>{1}</message>.", file_name, str(e)),
                              title = i18n_catalog.i18nc("@info:title", "Can't Open Project File"),
                              message_type = Message.MessageType.ERROR)
            message.show()
            self.setWorkspaceName("")
            return [], {}

        cura_file_names = [name for name in archive.namelist() if name.startswith("Cura/")]

        # Create a shadow copy of the preferences (We don't want all of the preferences, but we do want to re-use its
        # parsing code.
        temp_preferences = Preferences()
        try:
            serialized = archive.open("Cura/preferences.cfg").read().decode("utf-8")
        except KeyError as e:
            # If there is no preferences file, it's not a workspace, so notify user of failure.
            Logger.log("w", "File %s is not a valid workspace.", file_name)
            message = Message(i18n_catalog.i18nc("@info:error Don't translate the XML tags <filename> or <message>!",
                                                 "Project file <filename>{0}</filename> is corrupt: <message>{1}</message>.",
                                                 file_name, str(e)),
                              title=i18n_catalog.i18nc("@info:title", "Can't Open Project File"),
                              message_type=Message.MessageType.ERROR)
            message.show()
            self.setWorkspaceName("")
            return [], {}
        temp_preferences.deserialize(serialized)

        # Copy a number of settings from the temp preferences to the global
        global_preferences = application.getInstance().getPreferences()

        visible_settings = temp_preferences.getValue("general/visible_settings")
        if visible_settings is None:
            Logger.log("w", "Workspace did not contain visible settings. Leaving visibility unchanged")
        else:
            global_preferences.setValue("general/visible_settings", visible_settings)
            global_preferences.setValue("cura/active_setting_visibility_preset", "custom")

        categories_expanded = temp_preferences.getValue("cura/categories_expanded")
        if categories_expanded is None:
            Logger.log("w", "Workspace did not contain expanded categories. Leaving them unchanged")
        else:
            global_preferences.setValue("cura/categories_expanded", categories_expanded)

        application.expandedCategoriesChanged.emit()  # Notify the GUI of the change

        # If there are no machines of the same type, create a new machine.
        if self._resolve_strategies["machine"] != "override" or self._dialog.updatableMachinesModel.count == 0:
            # We need to create a new machine
            machine_name = self._container_registry.uniqueName(self._machine_info.name)

            # Printers with modifiable number of extruders (such as CFFF) will specify a machine_extruder_count in their
            # quality_changes file. If that's the case, take the extruder count into account when creating the machine
            # or else the extruderList will return only the first extruder, leading to missing non-global settings in
            # the other extruders.
            machine_extruder_count: Optional[int] = self._getMachineExtruderCount()
            global_stack = CuraStackBuilder.createMachine(machine_name, self._machine_info.definition_id, machine_extruder_count)
            if global_stack:  # Only switch if creating the machine was successful.
                extruder_stack_dict = {str(position): extruder for position, extruder in enumerate(global_stack.extruderList)}

                self._container_registry.addContainer(global_stack)
        else:
            # Find the machine which will be overridden
            global_stacks = self._container_registry.findContainerStacks(id = self._dialog.getMachineToOverride(), type = "machine")
            if not global_stacks:
                message = Message(i18n_catalog.i18nc("@info:error Don't translate the XML tag <filename>!",
                                                     "Project file <filename>{0}</filename> is made using profiles that are unknown to this version of UltiMaker Cura.", file_name),
                                  message_type = Message.MessageType.ERROR)
                message.show()
                self.setWorkspaceName("")
                return [], {}
            global_stack = global_stacks[0]
            extruder_stacks = self._container_registry.findContainerStacks(machine = global_stack.getId(),
                                                                           type = "extruder_train")
            extruder_stack_dict = {stack.getMetaDataEntry("position"): stack for stack in extruder_stacks}

            # Make sure that those extruders have the global stack as the next stack or later some value evaluation
            # will fail.
            for stack in extruder_stacks:
                stack.setNextStack(global_stack, connect_signals = False)

        if not self._is_ucp:
            Logger.log("d", "Workspace loading is checking definitions...")
            # Get all the definition files & check if they exist. If not, add them.
            definition_container_files = [name for name in cura_file_names if name.endswith(self._definition_container_suffix)]
            for definition_container_file in definition_container_files:
                container_id = self._stripFileToId(definition_container_file)

                definitions = self._container_registry.findDefinitionContainersMetadata(id = container_id)
                if not definitions:
                    definition_container = DefinitionContainer(container_id)
                    try:
                        definition_container.deserialize(archive.open(definition_container_file).read().decode("utf-8"),
                                                         file_name = definition_container_file)
                    except ContainerFormatError:
                        # We cannot just skip the definition file because everything else later will just break if the
                        # machine definition cannot be found.
                        Logger.logException("e", "Failed to deserialize definition file %s in project file %s",
                                            definition_container_file, file_name)
                        definition_container = self._container_registry.findDefinitionContainers(id = "fdmprinter")[0] #Fall back to defaults.
                    self._container_registry.addContainer(definition_container)
                Job.yieldThread()
                QCoreApplication.processEvents()  # Ensure that the GUI does not freeze.

            Logger.log("d", "Workspace loading is checking materials...")
            # Get all the material files and check if they exist. If not, add them.
            xml_material_profile = self._getXmlProfileClass()
            if self._material_container_suffix is None:
                self._material_container_suffix = ContainerRegistry.getMimeTypeForContainer(xml_material_profile).suffixes[0]
            if xml_material_profile:
                material_container_files = [name for name in cura_file_names if name.endswith(self._material_container_suffix)]
                for material_container_file in material_container_files:
                    to_deserialize_material = False
                    container_id = self._stripFileToId(material_container_file)
                    need_new_name = False
                    materials = self._container_registry.findInstanceContainers(id = container_id)

                    if not materials:
                        # No material found, deserialize this material later and add it
                        to_deserialize_material = True
                    else:
                        material_container = materials[0]
                        old_material_root_id = material_container.getMetaDataEntry("base_file")
                        if old_material_root_id is not None and not self._container_registry.isReadOnly(old_material_root_id):  # Only create new materials if they are not read only.
                            to_deserialize_material = True

                            if self._resolve_strategies["material"] == "override":
                                # Remove the old materials and then deserialize the one from the project
                                root_material_id = material_container.getMetaDataEntry("base_file")
                                application.getContainerRegistry().removeContainer(root_material_id)
                            elif self._resolve_strategies["material"] == "new":
                                # Note that we *must* deserialize it with a new ID, as multiple containers will be
                                # auto created & added.
                                container_id = self.getNewId(container_id)
                                self._old_new_materials[old_material_root_id] = container_id
                                need_new_name = True

                    if to_deserialize_material:
                        material_container = xml_material_profile(container_id)
                        try:
                            material_container.deserialize(archive.open(material_container_file).read().decode("utf-8"),
                                                           file_name = container_id + "." + self._material_container_suffix)
                        except ContainerFormatError:
                            Logger.logException("e", "Failed to deserialize material file %s in project file %s",
                                                material_container_file, file_name)
                            continue
                        if need_new_name:
                            new_name = ContainerRegistry.getInstance().uniqueName(material_container.getName())
                            material_container.setName(new_name)
                        material_container.setDirty(True)
                        self._container_registry.addContainer(material_container)
                    Job.yieldThread()
                    QCoreApplication.processEvents()  # Ensure that the GUI does not freeze.

        if global_stack:
            if not self._is_ucp:
                # Handle quality changes if any
                self._processQualityChanges(global_stack)

                # Prepare the machine
                self._applyChangesToMachine(global_stack, extruder_stack_dict)

            Logger.log("d", "Workspace loading is notifying rest of the code of changes...")
            # Actually change the active machine.
            #
            # This is scheduled for later is because it depends on the Variant/Material/Qualitiy Managers to have the latest
            # data, but those managers will only update upon a container/container metadata changed signal. Because this
            # function is running on the main thread (Qt thread), although those "changed" signals have been emitted, but
            # they won't take effect until this function is done.
            # To solve this, we schedule _updateActiveMachine() for later so it will have the latest data.

            self._updateActiveMachine(global_stack)

            if self._is_ucp:
                # Now we have switched, apply the user settings
                self._applyUserSettings(global_stack, extruder_stack_dict, self._user_settings)

        # Load all the nodes / mesh data of the workspace
        nodes = self._3mf_mesh_reader.read(file_name)
        if nodes is None:
            nodes = []

        if self._is_ucp:
            # We might be on a different printer than the one this project was made on.
            # The offset to the printers' center isn't saved; instead, try to just fit everything on the buildplate.
            full_extents = None
            for node in nodes:
                extents = node.getMeshData().getExtents() if node.getMeshData() else None
                if extents is not None:
                    pos = node.getPosition()
                    node_box = AxisAlignedBox(extents.minimum + pos, extents.maximum + pos)
                    if full_extents is None:
                        full_extents = node_box
                    else:
                        full_extents = full_extents + node_box
            if full_extents and full_extents.isValid():
                for node in nodes:
                    pos = node.getPosition()
                    node.setPosition(Vector(pos.x - full_extents.center.x, pos.y, pos.z - full_extents.center.z))

        base_file_name = os.path.basename(file_name)
        self.setWorkspaceName(base_file_name)

        self._is_ucp = None
        return nodes, self._loadMetadata(file_name)

    @staticmethod
    def _loadMetadata(file_name: str) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = dict()
        try:
            archive = zipfile.ZipFile(file_name, "r")
        except zipfile.BadZipFile:
            Logger.logException("w", "Unable to retrieve metadata from {fname}: 3MF archive is corrupt.".format(fname = file_name))
            return result
        except EnvironmentError as e:
            Logger.logException("w", "Unable to retrieve metadata from {fname}: File is inaccessible. Error: {err}".format(fname = file_name, err = str(e)))
            return result

        metadata_files = [name for name in archive.namelist() if name.endswith("plugin_metadata.json")]

        for metadata_file in metadata_files:
            try:
                plugin_id = metadata_file.split("/")[0]
                result[plugin_id] = json.loads(archive.open("%s/plugin_metadata.json" % plugin_id).read().decode("utf-8"))
            except Exception:
                Logger.logException("w", "Unable to retrieve metadata for %s", metadata_file)

        return result

    def _processQualityChanges(self, global_stack):
        if self._machine_info.quality_changes_info is None:
            return

        # If we have custom profiles, load them
        quality_changes_name = self._machine_info.quality_changes_info.name
        if self._machine_info.quality_changes_info is not None:
            Logger.log("i", "Loading custom profile [%s] from project file",
                       self._machine_info.quality_changes_info.name)

            # Get the correct extruder definition IDs for quality changes
            machine_definition_id_for_quality = ContainerTree.getInstance().machines[global_stack.definition.getId()].quality_definition
            machine_definition_for_quality = self._container_registry.findDefinitionContainers(id = machine_definition_id_for_quality)[0]

            quality_changes_info = self._machine_info.quality_changes_info
            quality_changes_quality_type = quality_changes_info.global_info.parser["metadata"]["quality_type"]

            # quality changes container may not be present for every extruder. Prepopulate the dict with default values.
            quality_changes_intent_category_per_extruder = {position: "default" for position in self._machine_info.extruder_info_dict}
            for position, info in quality_changes_info.extruder_info_dict.items():
                quality_changes_intent_category_per_extruder[position] = info.parser["metadata"].get("intent_category", "default")

            quality_changes_name = quality_changes_info.name
            create_new = self._resolve_strategies.get("quality_changes") != "override"
            if create_new:
                container_info_dict = {None: self._machine_info.quality_changes_info.global_info}
                container_info_dict.update(quality_changes_info.extruder_info_dict)

                quality_changes_name = self._container_registry.uniqueName(quality_changes_name)
                for position, container_info in container_info_dict.items():
                    extruder_stack = None
                    intent_category: Optional[str] = None
                    if position is not None:
                        try:
                            extruder_stack = global_stack.extruderList[int(position)]
                        except IndexError:
                            continue
                        intent_category = quality_changes_intent_category_per_extruder[position]
                    container = self._createNewQualityChanges(quality_changes_quality_type, intent_category, quality_changes_name, global_stack, extruder_stack)
                    container_info.container = container
                    self._container_registry.addContainer(container)

                    Logger.log("d", "Created new quality changes container [%s]", container.getId())

            else:
                # Find the existing containers
                quality_changes_containers = self._container_registry.findInstanceContainers(name = quality_changes_name,
                                                                                             type = "quality_changes")
                for container in quality_changes_containers:
                    extruder_position = container.getMetaDataEntry("position")
                    if extruder_position is None:
                        quality_changes_info.global_info.container = container
                    else:
                        if extruder_position not in quality_changes_info.extruder_info_dict:
                            quality_changes_info.extruder_info_dict[extruder_position] = ContainerInfo(None, None, None)
                        container_info = quality_changes_info.extruder_info_dict[extruder_position]
                        container_info.container = container

            # If there is no quality changes for any extruder, create one.
            if not quality_changes_info.extruder_info_dict:
                container_info = ContainerInfo(None, None, None)
                quality_changes_info.extruder_info_dict["0"] = container_info
                # If the global stack we're "targeting" has never been active, but was updated from Cura 3.4,
                # it might not have its extruders set properly.
                if len(global_stack.extruderList) == 0:
                    ExtruderManager.getInstance().fixSingleExtrusionMachineExtruderDefinition(global_stack)
                try:
                    extruder_stack = global_stack.extruderList[0]
                except IndexError:
                    extruder_stack = None
                intent_category = quality_changes_intent_category_per_extruder["0"]

                container = self._createNewQualityChanges(quality_changes_quality_type, intent_category, quality_changes_name, global_stack, extruder_stack)
                container_info.container = container
                self._container_registry.addContainer(container)

                Logger.log("d", "Created new quality changes container [%s]", container.getId())

            # Clear all existing containers
            quality_changes_info.global_info.container.clear()
            for container_info in quality_changes_info.extruder_info_dict.values():
                if container_info.container:
                    container_info.container.clear()

            # Loop over everything and override the existing containers
            global_info = quality_changes_info.global_info
            global_info.container.clear()  # Clear all
            for key, value in global_info.parser["values"].items():
                if not machine_definition_for_quality.getProperty(key, "settable_per_extruder"):
                    global_info.container.setProperty(key, "value", value)
                else:
                    quality_changes_info.extruder_info_dict["0"].container.setProperty(key, "value", value)

            for position, container_info in quality_changes_info.extruder_info_dict.items():
                if container_info.parser is None:
                    continue

                if container_info.container is None:
                    try:
                        extruder_stack = global_stack.extruderList[int(position)]
                    except IndexError:
                        continue
                    intent_category = quality_changes_intent_category_per_extruder[position]
                    container = self._createNewQualityChanges(quality_changes_quality_type, intent_category, quality_changes_name, global_stack, extruder_stack)
                    container_info.container = container
                    self._container_registry.addContainer(container)

                for key, value in container_info.parser["values"].items():
                    container_info.container.setProperty(key, "value", value)

        self._machine_info.quality_changes_info.name = quality_changes_name

    def _getMachineExtruderCount(self) -> Optional[int]:
        """
        Extracts the machine extruder count from the definition_changes file of the printer. If it is not specified in
        the file, None is returned instead.

        :return: The count of the machine's extruders
        """
        machine_extruder_count = None
        if self._machine_info \
                and self._machine_info.definition_changes_info \
                and "values" in self._machine_info.definition_changes_info.parser \
                and "machine_extruder_count" in self._machine_info.definition_changes_info.parser["values"]:
            try:
                # Theoretically, if the machine_extruder_count is a setting formula (e.g. "=3"), this will produce a
                # value error and the project file loading will load the settings in the first extruder only.
                # This is not expected to happen though, since all machine definitions define the machine_extruder_count
                # as an integer.
                machine_extruder_count = int(self._machine_info.definition_changes_info.parser["values"]["machine_extruder_count"])
            except ValueError:
                Logger.log("w", "'machine_extruder_count' in file '{file_name}' is not a number."
                           .format(file_name = self._machine_info.definition_changes_info.file_name))
        return machine_extruder_count

    def _createNewQualityChanges(self, quality_type: str, intent_category: Optional[str], name: str, global_stack: GlobalStack, extruder_stack: Optional[ExtruderStack]) -> InstanceContainer:
        """Helper class to create a new quality changes profile.

        This will then later be filled with the appropriate data.

        :param quality_type: The quality type of the new profile.
        :param intent_category: The intent category of the new profile.
        :param name: The name for the profile. This will later be made unique so
            it doesn't need to be unique yet.
        :param global_stack: The global stack showing the configuration that the
            profile should be created for.
        :param extruder_stack: The extruder stack showing the configuration that
            the profile should be created for. If this is None, it will be created
            for the global stack.
        """

        container_registry = CuraApplication.getInstance().getContainerRegistry()
        base_id = global_stack.definition.getId() if extruder_stack is None else extruder_stack.getId()
        new_id = base_id + "_" + name
        new_id = new_id.lower().replace(" ", "_")
        new_id = container_registry.uniqueName(new_id)

        # Create a new quality_changes container for the quality.
        quality_changes = InstanceContainer(new_id)
        quality_changes.setName(name)
        quality_changes.setMetaDataEntry("type", "quality_changes")
        quality_changes.setMetaDataEntry("quality_type", quality_type)
        if intent_category is not None:
            quality_changes.setMetaDataEntry("intent_category", intent_category)

        # If we are creating a container for an extruder, ensure we add that to the container.
        if extruder_stack is not None:
            quality_changes.setMetaDataEntry("position", extruder_stack.getMetaDataEntry("position"))

        # If the machine specifies qualities should be filtered, ensure we match the current criteria.
        machine_definition_id = ContainerTree.getInstance().machines[global_stack.definition.getId()].quality_definition
        quality_changes.setDefinition(machine_definition_id)

        quality_changes.setMetaDataEntry("setting_version", CuraApplication.getInstance().SettingVersion)
        quality_changes.setDirty(True)
        return quality_changes

    @staticmethod
    def _clearStack(stack):
        application = CuraApplication.getInstance()

        stack.definitionChanges.clear()
        stack.variant = application.empty_variant_container
        stack.material = application.empty_material_container
        stack.quality = application.empty_quality_container
        stack.qualityChanges = application.empty_quality_changes_container
        stack.userChanges.clear()

    def _applyDefinitionChanges(self, global_stack, extruder_stack_dict):
        values_to_set_for_extruders = {}
        if self._machine_info.definition_changes_info is not None:
            parser = self._machine_info.definition_changes_info.parser
            for key, value in parser["values"].items():
                if global_stack.getProperty(key, "settable_per_extruder"):
                    values_to_set_for_extruders[key] = value
                else:
                    if not self._settingIsFromMissingPackage(key, value):
                        global_stack.definitionChanges.setProperty(key, "value", value)

        for position, extruder_stack in extruder_stack_dict.items():
            if position not in self._machine_info.extruder_info_dict:
                continue

            extruder_info = self._machine_info.extruder_info_dict[position]
            if extruder_info.definition_changes_info is None:
                continue
            parser = extruder_info.definition_changes_info.parser
            for key, value in values_to_set_for_extruders.items():
                extruder_stack.definitionChanges.setProperty(key, "value", value)
            if parser is not None:
                for key, value in parser["values"].items():
                    if not self._settingIsFromMissingPackage(key, value):
                        extruder_stack.definitionChanges.setProperty(key, "value", value)

    def _applyUserChanges(self, global_stack, extruder_stack_dict):
        values_to_set_for_extruder_0 = {}
        if self._machine_info.user_changes_info is not None:
            parser = self._machine_info.user_changes_info.parser
            for key, value in parser["values"].items():
                if global_stack.getProperty(key, "settable_per_extruder"):
                    values_to_set_for_extruder_0[key] = value
                else:
                    if not self._settingIsFromMissingPackage(key, value):
                        global_stack.userChanges.setProperty(key, "value", value)

        for position, extruder_stack in extruder_stack_dict.items():
            if position not in self._machine_info.extruder_info_dict:
                continue

            extruder_info = self._machine_info.extruder_info_dict[position]
            if extruder_info.user_changes_info is not None:
                parser = self._machine_info.extruder_info_dict[position].user_changes_info.parser
                if position == "0":
                    for key, value in values_to_set_for_extruder_0.items():
                        extruder_stack.userChanges.setProperty(key, "value", value)
                if parser is not None:
                    for key, value in parser["values"].items():
                        if not self._settingIsFromMissingPackage(key, value):
                            extruder_stack.userChanges.setProperty(key, "value", value)

    def _applyVariants(self, global_stack, extruder_stack_dict):
        machine_node = ContainerTree.getInstance().machines[global_stack.definition.getId()]

        # Take the global variant from the machine info if available.
        if self._machine_info.variant_info is not None:
            variant_name = self._machine_info.variant_info.parser["general"]["name"]
            if variant_name in machine_node.variants:
                global_stack.variant = machine_node.variants[variant_name].container
            else:
                Logger.log("w", "Could not find global variant '{0}'.".format(variant_name))

        for position, extruder_stack in extruder_stack_dict.items():
            if position not in self._machine_info.extruder_info_dict:
                continue
            extruder_info = self._machine_info.extruder_info_dict[position]
            if extruder_info.variant_info is None:
                # If there is no variant_info, try to use the default variant. Otherwise, any available variant.
                node = machine_node.variants.get(machine_node.preferred_variant_name, next(iter(machine_node.variants.values())))
            else:
                variant_name = extruder_info.variant_info.parser["general"]["name"]
                node = ContainerTree.getInstance().machines[global_stack.definition.getId()].variants.get(variant_name, next(iter(machine_node.variants.values())))
            extruder_stack.variant = node.container

    def _applyMaterials(self, global_stack, extruder_stack_dict):
        machine_node = ContainerTree.getInstance().machines[global_stack.definition.getId()]
        for position, extruder_stack in extruder_stack_dict.items():
            if position not in self._machine_info.extruder_info_dict:
                continue
            extruder_info = self._machine_info.extruder_info_dict[position]
            if extruder_info.root_material_id is None:
                continue

            root_material_id = extruder_info.root_material_id
            root_material_id = self._old_new_materials.get(root_material_id, root_material_id)

            available_materials = machine_node.variants[extruder_stack.variant.getName()].materials
            if root_material_id not in available_materials:
                continue
            material_node = available_materials[root_material_id]
            extruder_stack.material = material_node.container

    def _clearMachineSettings(self, global_stack, extruder_stack_dict):
        self._clearStack(global_stack)
        for extruder_stack in extruder_stack_dict.values():
            self._clearStack(extruder_stack)

        self._quality_changes_to_apply = None
        self._quality_type_to_apply = None
        self._intent_category_to_apply = None
        self._user_settings_to_apply = None

    def _applyUserSettings(self, global_stack, extruder_stack_dict, user_settings):
        for stack_name, settings in user_settings.items():
            if stack_name == 'global':
                ThreeMFWorkspaceReader._applyUserSettingsOnStack(global_stack, settings)
            else:
                extruder_match = re.fullmatch('extruder_([0-9]+)', stack_name)
                if extruder_match is not None:
                    extruder_nr = extruder_match.group(1)
                    if extruder_nr in extruder_stack_dict:
                        ThreeMFWorkspaceReader._applyUserSettingsOnStack(extruder_stack_dict[extruder_nr], settings)

    @staticmethod
    def _applyUserSettingsOnStack(stack, user_settings):
        user_settings_container = stack.userChanges

        for setting_to_import, setting_value in user_settings.items():
            user_settings_container.setProperty(setting_to_import, 'value', setting_value)

    def _applyChangesToMachine(self, global_stack, extruder_stack_dict):
        # Clear all first
        self._clearMachineSettings(global_stack, extruder_stack_dict)

        self._applyDefinitionChanges(global_stack, extruder_stack_dict)
        self._applyUserChanges(global_stack, extruder_stack_dict)
        self._applyVariants(global_stack, extruder_stack_dict)
        self._applyMaterials(global_stack, extruder_stack_dict)

        # prepare the quality to select
        if self._machine_info.quality_changes_info is not None:
            self._quality_changes_to_apply = self._machine_info.quality_changes_info.name
        else:
            self._quality_type_to_apply = self._machine_info.quality_type
            self._intent_category_to_apply = self._machine_info.intent_category

        # Set enabled/disabled for extruders
        for position, extruder_stack in extruder_stack_dict.items():
            extruder_info = self._machine_info.extruder_info_dict.get(position)
            if not extruder_info:
                continue
            if "enabled" not in extruder_stack.getMetaData():
                extruder_stack.setMetaDataEntry("enabled", "True")
            extruder_stack.setMetaDataEntry("enabled", str(extruder_info.enabled))

        # Set metadata fields that are missing from the global stack
        for key, value in self._machine_info.metadata_dict.items():
            if key not in _ignored_machine_network_metadata:
                global_stack.setMetaDataEntry(key, value)

    def _settingIsFromMissingPackage(self, key, value):
        # Check if the key and value pair is from the missing package
        for package in self._dialog.missingPackages:
            if value.startswith("PLUGIN::"):
                if (package['id'] + "@" + package['package_version']) in value:
                    Logger.log("w", f"Ignoring {key} value {value} from missing package")
                    return True
        return False

    def _updateActiveMachine(self, global_stack):
        # Actually change the active machine.
        machine_manager = Application.getInstance().getMachineManager()
        container_tree = ContainerTree.getInstance()

        machine_manager.setActiveMachine(global_stack.getId())

        # Set metadata fields that are missing from the global stack
        if not self._is_ucp:
            for key, value in self._machine_info.metadata_dict.items():
                if key not in global_stack.getMetaData() and key not in _ignored_machine_network_metadata:
                    global_stack.setMetaDataEntry(key, value)

            if self._quality_changes_to_apply !=None:
                quality_changes_group_list = container_tree.getCurrentQualityChangesGroups()
                quality_changes_group = next((qcg for qcg in quality_changes_group_list if qcg.name == self._quality_changes_to_apply), None)
                if not quality_changes_group:
                    Logger.log("e", "Could not find quality_changes [%s]", self._quality_changes_to_apply)
                    return
                machine_manager.setQualityChangesGroup(quality_changes_group, no_dialog = True)
            else:
                quality_group_dict = container_tree.getCurrentQualityGroups()
                if self._quality_type_to_apply in quality_group_dict:
                    quality_group = quality_group_dict[self._quality_type_to_apply]
                else:
                    Logger.log("i", "Could not find quality type [%s], switch to default", self._quality_type_to_apply)
                    preferred_quality_type = global_stack.getMetaDataEntry("preferred_quality_type")
                    quality_group = quality_group_dict.get(preferred_quality_type)
                    if quality_group is None:
                        Logger.log("e", "Could not get preferred quality type [%s]", preferred_quality_type)

                if quality_group is not None:
                    machine_manager.setQualityGroup(quality_group, no_dialog = True)

                    # Also apply intent if available
                    available_intent_category_list = IntentManager.getInstance().currentAvailableIntentCategories()
                    if self._intent_category_to_apply is not None and self._intent_category_to_apply in available_intent_category_list:
                        machine_manager.setIntentByCategory(self._intent_category_to_apply)
                    else:
                        # if no intent is provided, reset to the default (balanced) intent
                        machine_manager.resetIntents()
        # Notify everything/one that is to notify about changes.
        global_stack.containersChanged.emit(global_stack.getTop())

    @staticmethod
    def _stripFileToId(file):
        mime_type = MimeTypeDatabase.getMimeTypeForFile(file)
        file = mime_type.stripExtension(file)
        return file.replace("Cura/", "")

    def _getXmlProfileClass(self):
        return self._container_registry.getContainerForMimeType(MimeTypeDatabase.getMimeType("application/x-ultimaker-material-profile"))

    @staticmethod
    def _getContainerIdListFromSerialized(serialized):
        """Get the list of ID's of all containers in a container stack by partially parsing it's serialized data."""

        parser = ConfigParser(interpolation = None, empty_lines_in_values = False)
        parser.read_string(serialized)

        container_ids = []
        if "containers" in parser:
            for index, container_id in parser.items("containers"):
                container_ids.append(container_id)
        elif parser.has_option("general", "containers"):
            container_string = parser["general"].get("containers", "")
            container_list = container_string.split(",")
            container_ids = [container_id for container_id in container_list if container_id != ""]

        # HACK: there used to be 6 containers numbering from 0 to 5 in a stack,
        #       now we have 7: index 5 becomes "definition_changes"
        if len(container_ids) == 6:
            # Hack; We used to not save the definition changes. Fix this.
            container_ids.insert(5, "empty")

        return container_ids

    @staticmethod
    def _getMachineNameFromSerializedStack(serialized):
        parser = ConfigParser(interpolation = None, empty_lines_in_values = False)
        parser.read_string(serialized)
        return parser["general"].get("name", "")

    @staticmethod
    def _getMetaDataDictFromSerializedStack(serialized: str) -> Dict[str, str]:
        parser = ConfigParser(interpolation = None, empty_lines_in_values = False)
        parser.read_string(serialized)
        return dict(parser["metadata"])

    @staticmethod
    def _getMaterialLabelFromSerialized(serialized):
        data = ET.fromstring(serialized)
        metadata = data.iterfind("./um:metadata/um:name/um:label", {"um": "http://www.ultimaker.com/material"})
        for entry in metadata:
            return entry.text

    @staticmethod
    def _parse_packages_metadata(archive: zipfile.ZipFile) -> List[Dict[str, str]]:
        try:
            package_metadata = json.loads(archive.open("Cura/packages.json").read().decode("utf-8"))
            return package_metadata["packages"]
        except KeyError:
            Logger.warning("No package metadata was found in .3mf file.")
        except Exception:
            Logger.error("Failed to load packages metadata from .3mf file.")

        return []


    @staticmethod
    def _filter_missing_package_metadata(package_metadata: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Filters out installed packages from package_metadata"""
        missing_packages = []
        package_manager = cast(CuraPackageManager, CuraApplication.getInstance().getPackageManager())

        for package in package_metadata:
            package_id = package["id"]
            if not package_manager.isPackageInstalled(package_id):
                missing_packages.append(package)

        return missing_packages

