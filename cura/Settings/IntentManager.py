#Copyright (c) 2019 Ultimaker B.V.
#Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot
from typing import Any, Dict, List, Optional, Set, Tuple, TYPE_CHECKING

from UM.Logger import Logger
from UM.Settings.InstanceContainer import InstanceContainer

import cura.CuraApplication
from cura.Machines.ContainerTree import ContainerTree
from cura.Settings.cura_empty_instance_containers import empty_intent_container

if TYPE_CHECKING:
    from UM.Settings.InstanceContainer import InstanceContainer


##  Front-end for querying which intents are available for a certain
#   configuration.
class IntentManager(QObject):
    __instance = None

    ##  This class is a singleton.
    @classmethod
    def getInstance(cls):
        if not cls.__instance:
            cls.__instance = IntentManager()
        return cls.__instance

    intentCategoryChanged = pyqtSignal() #Triggered when we switch categories.

    ##  Gets the metadata dictionaries of all intent profiles for a given
    #   configuration.
    #
    #   \param definition_id ID of the printer.
    #   \param nozzle_name Name of the nozzle.
    #   \param material_base_file The base_file of the material.
    #   \return A list of metadata dictionaries matching the search criteria, or
    #   an empty list if nothing was found.
    def intentMetadatas(self, definition_id: str, nozzle_name: str, material_base_file: str) -> List[Dict[str, Any]]:
        intent_metadatas = []  # type: List[Dict[str, Any]]
        materials = ContainerTree.getInstance().machines[definition_id].variants[nozzle_name].materials
        if material_base_file not in materials:
            return intent_metadatas

        material_node = materials[material_base_file]
        for quality_node in material_node.qualities.values():
            for intent_node in quality_node.intents.values():
                intent_metadatas.append(intent_node.getMetadata())
        return intent_metadatas

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
        quality_groups = ContainerTree.getInstance().getCurrentQualityGroups()
        available_quality_types = {quality_group.quality_type for quality_group in quality_groups.values() if quality_group.node_for_global is not None}

        final_intent_ids = set()  # type: Set[str]
        current_definition_id = global_stack.definition.getId()
        for extruder_stack in global_stack.extruderList:
            if not extruder_stack.isEnabled:
                continue
            nozzle_name = extruder_stack.variant.getMetaDataEntry("name")
            material_id = extruder_stack.material.getMetaDataEntry("base_file")
            final_intent_ids |= {metadata["id"] for metadata in self.intentMetadatas(current_definition_id, nozzle_name, material_id) if metadata.get("quality_type") in available_quality_types}

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
        current_definition_id = global_stack.definition.getId()
        final_intent_categories = set()  # type: Set[str]
        for extruder_stack in global_stack.extruderList:
            if not extruder_stack.isEnabled:
                continue
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
        Logger.log("i", "Attempting to set intent_category to [%s] and quality type to [%s]", intent_category, quality_type)
        old_intent_category = self.currentIntentCategory
        application = cura.CuraApplication.CuraApplication.getInstance()
        global_stack = application.getGlobalContainerStack()
        if global_stack is None:
            return
        current_definition_id = global_stack.definition.getId()
        machine_node = ContainerTree.getInstance().machines[current_definition_id]
        for extruder_stack in global_stack.extruderList:
            nozzle_name = extruder_stack.variant.getMetaDataEntry("name")
            material_id = extruder_stack.material.getMetaDataEntry("base_file")

            material_node = machine_node.variants[nozzle_name].materials[material_id]

            # Since we want to switch to a certain quality type, check the tree if we have one.
            quality_node = None
            for q_node in material_node.qualities.values():
                if q_node.quality_type == quality_type:
                    quality_node = q_node

            if quality_node is None:
                Logger.log("w", "Unable to find quality_type [%s] for extruder [%s]", quality_type, extruder_stack.getId())
                continue

            # Check that quality node if we can find a matching intent.
            intent_id = None
            for id, intent_node in quality_node.intents.items():
                if intent_node.intent_category == intent_category:
                    intent_id = id
            intent = application.getContainerRegistry().findContainers(id = intent_id)
            if intent:
                extruder_stack.intent = intent[0]
            else:
                extruder_stack.intent = self.getDefaultIntent()
        application.getMachineManager().setQualityGroupByQualityType(quality_type)
        if old_intent_category != intent_category:
            self.intentCategoryChanged.emit()
