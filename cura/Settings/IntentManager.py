#Copyright (c) 2019 Ultimaker B.V.
#Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot
from typing import Any, Dict, List, Optional, Set, Tuple, TYPE_CHECKING
import cura.CuraApplication
from cura.Machines.QualityManager import getMachineDefinitionIDForQualitySearch
from cura.Machines.QualityNode import QualityNode
from cura.Settings.cura_empty_instance_containers import empty_intent_container
from cura.Settings.ExtruderStack import ExtruderStack
from UM.Logger import Logger
from UM.Settings.InstanceContainer import InstanceContainer

if TYPE_CHECKING:
    from cura.Machines.QualityChangesGroup import QualityChangesGroup
    from UM.Settings.InstanceContainer import InstanceContainer

##  Front-end for querying which intents are available for a certain
#   configuration.
class IntentManager(QObject):
    __instance = None

    # TODO: Find-out: QualityManager has a signal here, should this have a signal?

    def __init__(self) -> None:
        super().__init__()

        # For quality_changes lookup
        self._machine_quality_type_to_quality_changes_dict = {}  # type: Dict[str, QualityNode]

        cura.CuraApplication.CuraApplication.getInstance().getMachineManager().activeStackChanged.connect(self.configurationChanged)
        self.configurationChanged.connect(self.selectDefaultIntent)
        pass

    # TODO: Maybe this can be moved to __init__?
    def initialize(self) -> None:
        registry = cura.CuraApplication.CuraApplication.getInstance().getContainerRegistry()

        # Initialize the lookup tree for quality_changes profiles with following structure:
        # <machine> -> <quality_type> -> <name>
        quality_changes_metadata_list = registry.findContainersMetadata(type = "quality_changes")
        for metadata in quality_changes_metadata_list:
            if metadata["id"] == "empty_quality_changes":
                continue

            machine_definition_id = metadata["definition"]
            quality_type = metadata["quality_type"]

            if machine_definition_id not in self._machine_quality_type_to_quality_changes_dict:
                self._machine_quality_type_to_quality_changes_dict[machine_definition_id] = QualityNode()    ## TODO: What is a QualityNode?
            machine_node = self._machine_quality_type_to_quality_changes_dict[machine_definition_id]
            machine_node.addQualityChangesMetadata(quality_type, metadata)

        # TODO: QualityManager sent a signal (qualitiesUpdated) after the method (QM.initialize) this was moved from.

    ##  This class is a singleton.
    @classmethod
    def getInstance(cls):
        if not cls.__instance:
            cls.__instance = IntentManager()
        return cls.__instance

    configurationChanged = pyqtSignal() #Triggered when something changed in the rest of the stack.
    intentCategoryChanged = pyqtSignal() #Triggered when we switch categories.

    ##  Gets the metadata dictionaries of all intent profiles for a given
    #   configuration.
    #
    #   \param definition_id ID of the printer.
    #   \param nozzle_name Name of the nozzle.
    #   \param material_id ID of the material.
    #   \return A list of metadata dictionaries matching the search criteria, or
    #   an empty list if nothing was found.
    def intentMetadatas(self, definition_id: str, nozzle_name: str, material_id: str) -> List[Dict[str, Any]]:
        registry = cura.CuraApplication.CuraApplication.getInstance().getContainerRegistry()
        return registry.findContainersMetadata(type = "intent", definition = definition_id, variant = nozzle_name, material = material_id)

    ##  Collects and returns all intent categories available for the given
    #   parameters. Note that the 'default' category is always available.
    #
    #   \param definition_id ID of the printer.
    #   \param nozzle_name Name of the nozzle.
    #   \param material_id ID of the material.
    #   \return A set of intent category names.
    def intentCategories(self, definition_id: str, nozzle_id: str, material_id: str) -> List[str]:
        categories = set()
        for intent in self.intentMetadatas(definition_id, nozzle_id, material_id):
            categories.add(intent["intent_category"])
        categories.add("default") #The "empty" intent is not an actual profile specific to the configuration but we do want it to appear in the categories list.
        return list(categories)

    ##  List of intents to be displayed in the interface.
    #
    #   For the interface this will have to be broken up into the different
    #   intent categories. That is up to the model there.
    #
    #   \return A list of tuples of intent_category and quality_type. The actual
    #   instance may vary per extruder.
    def getCurrentAvailableIntents(self) -> List[Tuple[str, str]]:
        application = cura.CuraApplication.CuraApplication.getInstance()
        global_stack = application.getGlobalContainerStack()
        if global_stack is None:
            return [("default", "normal")]
            # TODO: We now do this (return a default) if the global stack is missing, but not in the code below,
            #       even though there should always be defaults. The problem then is what to do with the quality_types.
            #       Currently _also_ inconsistent with 'currentAvailableIntentCategories', which _does_ return default.
        quality_groups = application.getQualityManager().getQualityGroups(global_stack)
        available_quality_types = {quality_group.quality_type for quality_group in quality_groups.values() if quality_group.node_for_global is not None}

        final_intent_ids = set()  # type: Set[str]
        current_definition_id = global_stack.definition.getMetaDataEntry("id")
        for extruder_stack in global_stack.extruderList:
            nozzle_name = extruder_stack.variant.getMetaDataEntry("name")
            material_id = extruder_stack.material.getMetaDataEntry("base_file")
            final_intent_ids |= {metadata["id"] for metadata in self.intentMetadatas(current_definition_id, nozzle_name, material_id) if metadata["quality_type"] in available_quality_types}

        result = set()  # type: Set[Tuple[str, str]]
        for intent_id in final_intent_ids:
            intent_metadata = application.getContainerRegistry().findContainersMetadata(id = intent_id)[0]
            result.add((intent_metadata["intent_category"], intent_metadata["quality_type"]))
        return list(result)

    ##  List of intent categories available in either of the extruders.
    #
    #   This is purposefully inconsistent with the way that the quality types
    #   are listed. The quality types will show all quality types available in
    #   the printer using any configuration. This will only list the intent
    #   categories that are available using the current configuration (but the
    #   union over the extruders).
    #   \return List of all categories in the current configurations of all
    #   extruders.
    def currentAvailableIntentCategories(self) -> List[str]:
        global_stack = cura.CuraApplication.CuraApplication.getInstance().getGlobalContainerStack()
        if global_stack is None:
            return ["default"]
        current_definition_id = global_stack.definition.getMetaDataEntry("id")
        final_intent_categories = set()  # type: Set[str]
        for extruder_stack in global_stack.extruderList:
            nozzle_name = extruder_stack.variant.getMetaDataEntry("name")
            material_id = extruder_stack.material.getMetaDataEntry("base_file")
            final_intent_categories.update(self.intentCategories(current_definition_id, nozzle_name, material_id))
        return list(final_intent_categories)

    ##  The intent that gets selected by default when no intent is available for
    #   the configuration, an extruder can't match the intent that the user
    #   selects, or just when creating a new printer.
    def getDefaultIntent(self) -> InstanceContainer:
        return empty_intent_container

    @pyqtProperty(str, notify = intentCategoryChanged)
    def currentIntentCategory(self) -> str:
        application = cura.CuraApplication.CuraApplication.getInstance()
        active_extruder_stack = application.getMachineManager().activeStack
        if active_extruder_stack is None:
            return ""
        return active_extruder_stack.intent.getMetaDataEntry("intent_category", "")

    ##  Apply intent on the stacks.
    @pyqtSlot(str, str)
    def selectIntent(self, intent_category: str, quality_type: str) -> None:
        old_intent_category = self.currentIntentCategory
        application = cura.CuraApplication.CuraApplication.getInstance()
        global_stack = application.getGlobalContainerStack()
        if global_stack is None:
            return
        current_definition_id = global_stack.definition.getMetaDataEntry("id")
        for extruder_stack in global_stack.extruderList:
            nozzle_name = extruder_stack.variant.getMetaDataEntry("name")
            material_id = extruder_stack.material.getMetaDataEntry("base_file")
            intent = application.getContainerRegistry().findContainers(definition = current_definition_id, variant = nozzle_name, material = material_id, quality_type = quality_type, intent_category = intent_category)
            if intent:
                extruder_stack.intent = intent[0]
            else:
                extruder_stack.intent = self.getDefaultIntent()

        application.getMachineManager().setQualityGroupByQualityType(quality_type)
        if old_intent_category != intent_category:
            self.intentCategoryChanged.emit()

    ##  Selects the default intents on every extruder.
    def selectDefaultIntent(self) -> None:
        application = cura.CuraApplication.CuraApplication.getInstance()
        global_stack = application.getGlobalContainerStack()
        if global_stack is None:
            return
        for extruder_stack in global_stack.extruderList:
            extruder_stack.intent = self.getDefaultIntent()

    ## Returns a dict of "custom profile name" -> QualityChangesGroup
    def getQualityChangesGroups(self, machine: "GlobalStack") -> dict:
        application = cura.CuraApplication.CuraApplication.getInstance()
        machine_definition_id = getMachineDefinitionIDForQualitySearch(machine.definition)

        machine_node = self._machine_quality_type_to_quality_changes_dict.get(machine_definition_id)
        if not machine_node:
            Logger.log("i", "Cannot find node for machine def [%s] in QualityChanges lookup table", machine_definition_id)
            return dict()

        # Update availability for each QualityChangesGroup:
        # A custom profile is always available as long as the quality_type it's based on is available
        quality_group_dict = application.getQualityManager().getQualityGroups(machine)
        available_quality_type_list = [qt for qt, qg in quality_group_dict.items() if qg.is_available]

        # Iterate over all quality_types in the machine node
        quality_changes_group_dict = dict()
        for quality_type, quality_changes_node in machine_node.quality_type_map.items():
            for quality_changes_name, quality_changes_group in quality_changes_node.children_map.items():
                quality_changes_group_dict[quality_changes_name] = quality_changes_group
                quality_changes_group.is_available = quality_type in available_quality_type_list

        return quality_changes_group_dict


    # TODO: Some (all)? of  these where labeled 'Methods for GUI' in QualityManager where they where copied from, probably should move [most|all] of them.

    #
    # Remove the given quality changes group.
    #
    @pyqtSlot(QObject)
    def removeQualityChangesGroup(self, quality_changes_group: "QualityChangesGroup") -> None:
        Logger.log("i", "Removing quality changes group [%s]", quality_changes_group.name)
        registry = cura.CuraApplication.CuraApplication.getInstance().getContainerRegistry()

        removed_quality_changes_ids = set()
        for node in quality_changes_group.getAllNodes():
            container_id = node.getMetaDataEntry("id")
            registry.removeContainer(container_id)
            removed_quality_changes_ids.add(container_id)

        # Reset all machines that have activated this quality changes to empty.
        for global_stack in registry.findContainerStacks(type = "machine"):
            if global_stack.qualityChanges.getId() in removed_quality_changes_ids:
                global_stack.qualityChanges = self._empty_quality_changes_container
        for extruder_stack in registry.findContainerStacks(type = "extruder_train"):
            if extruder_stack.qualityChanges.getId() in removed_quality_changes_ids:
                extruder_stack.qualityChanges = self._empty_quality_changes_container

    #
    # Rename a set of quality changes containers. Returns the new name.
    #
    @pyqtSlot(QObject, str, result = str)
    def renameQualityChangesGroup(self, quality_changes_group: "QualityChangesGroup", new_name: str) -> str:
        Logger.log("i", "Renaming QualityChangesGroup[%s] to [%s]", quality_changes_group.name, new_name)
        if new_name == quality_changes_group.name:
            Logger.log("i", "QualityChangesGroup name [%s] unchanged.", quality_changes_group.name)
            return new_name

        registry = cura.CuraApplication.CuraApplication.getInstance().getContainerRegistry()
        application = cura.CuraApplication.CuraApplication.getInstance()

        new_name = registry.uniqueName(new_name)
        for node in quality_changes_group.getAllNodes():
            container = node.getContainer()
            if container:
                container.setName(new_name)

        quality_changes_group.name = new_name

        application.getMachineManager().activeQualityChanged.emit()
        application.getMachineManager().activeQualityGroupChanged.emit()

        return new_name

    #
    # Duplicates the given quality.
    #
    @pyqtSlot(str, "QVariantMap")
    def duplicateQualityChanges(self, quality_changes_name: str, quality_model_item) -> None:
        registry = cura.CuraApplication.CuraApplication.getInstance().getContainerRegistry()
        global_stack = cura.CuraApplication.CuraApplication.getInstance().getGlobalContainerStack()
        if not global_stack:
            Logger.log("i", "No active global stack, cannot duplicate quality changes.")
            return

        quality_group = quality_model_item["quality_group"]
        quality_changes_group = quality_model_item["quality_changes_group"]
        if quality_changes_group is None:
            # create global quality changes only
            new_name = registry.uniqueName(quality_changes_name)
            new_quality_changes = self._createQualityChanges(quality_group.quality_type, new_name,
                                                             global_stack, None)
            registry.addContainer(new_quality_changes)
        else:
            new_name = registry.uniqueName(quality_changes_name)
            for node in quality_changes_group.getAllNodes():
                container = node.getContainer()
                if not container:
                    continue
                new_id = registry.uniqueName(container.getId())
                registry.addContainer(container.duplicate(new_id, new_name))

    ##  Create quality changes containers from the user containers in the active stacks.
    #
    #   This will go through the global and extruder stacks and create quality_changes containers from
    #   the user containers in each stack. These then replace the quality_changes containers in the
    #   stack and clear the user settings.
    @pyqtSlot(str)
    def createQualityChanges(self, base_name: str) -> None:
        machine_manager = cura.CuraApplication.CuraApplication.getInstance().getMachineManager()

        global_stack = machine_manager.activeMachine
        if not global_stack:
            return

        active_quality_name = machine_manager.activeQualityOrQualityChangesName
        if active_quality_name == "":
            Logger.log("w", "No quality container found in stack %s, cannot create profile", global_stack.getId())
            return

        registry = cura.CuraApplication.CuraApplication.getInstance().getContainerRegistry()

        machine_manager.blurSettings.emit()
        if base_name is None or base_name == "":
            base_name = active_quality_name
        unique_name = registry.uniqueName(base_name)

        # Go through the active stacks and create quality_changes containers from the user containers.
        stack_list = [global_stack] + list(global_stack.extruders.values())
        for stack in stack_list:
            user_container = stack.userChanges
            quality_container = stack.quality
            quality_changes_container = stack.qualityChanges
            if not quality_container or not quality_changes_container:
                Logger.log("w", "No quality or quality changes container found in stack %s, ignoring it", stack.getId())
                continue

            quality_type = quality_container.getMetaDataEntry("quality_type")
            extruder_stack = None
            if isinstance(stack, ExtruderStack):
                extruder_stack = stack
            new_changes = self._createQualityChanges(quality_type, unique_name, global_stack, extruder_stack)
            from cura.Settings.ContainerManager import ContainerManager
            ContainerManager.getInstance()._performMerge(new_changes, quality_changes_container, clear_settings = False)
            ContainerManager.getInstance()._performMerge(new_changes, user_container)

            registry.addContainer(new_changes)

    #
    # Create a quality changes container with the given setup.
    #
    def _createQualityChanges(self, quality_type: str, new_name: str, machine: "GlobalStack",
                              extruder_stack: Optional["ExtruderStack"]) -> "InstanceContainer":
        base_id = machine.definition.getId() if extruder_stack is None else extruder_stack.getId()
        new_id = base_id + "_" + new_name
        new_id = new_id.lower().replace(" ", "_")
        new_id = self._container_registry.uniqueName(new_id)

        # Create a new quality_changes container for the quality.
        quality_changes = InstanceContainer(new_id)
        quality_changes.setName(new_name)
        quality_changes.setMetaDataEntry("type", "quality_changes")
        quality_changes.setMetaDataEntry("quality_type", quality_type)

        # If we are creating a container for an extruder, ensure we add that to the container
        if extruder_stack is not None:
            quality_changes.setMetaDataEntry("position", extruder_stack.getMetaDataEntry("position"))

        # If the machine specifies qualities should be filtered, ensure we match the current criteria.
        machine_definition_id = cura.CuraApplication.CuraApplication.getInstance().getQualityManager().getMachineDefinitionIDForQualitySearch(machine.definition)
        quality_changes.setDefinition(machine_definition_id)

        quality_changes.setMetaDataEntry("setting_version", self._application.SettingVersion)
        return quality_changes