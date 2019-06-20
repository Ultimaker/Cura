#Copyright (c) 2019 Ultimaker B.V.
#Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty, pyqtSignal
from typing import Any, Dict, List, Tuple, TYPE_CHECKING
from cura.CuraApplication import CuraApplication
from cura.Machines.QualityManager import QualityManager
from cura.Settings.MachineManager import MachineManager
from UM.Settings.ContainerRegistry import ContainerRegistry

if TYPE_CHECKING:
    from UM.Settings.InstanceContainer import InstanceContainer

##  Front-end for querying which intents are available for a certain
#   configuration.
#
#   CURRENTLY THIS CLASS CONTAINS ONLY SOME PSEUDOCODE OF WHAT WE ARE SUPPOSED
#   TO IMPLEMENT.
class IntentManager:
    __instance = None

    def __init__(self) -> None:
        MachineManager.activeStackChanged.connect(self.configurationChanged)
        self.configurationChanged.connect(self.selectDefaultIntent)
        pass

    ##  This class is a singleton.
    @classmethod
    def getInstance(cls):
        if not cls.__instance:
            cls.__instance = IntentManager()
        return cls.__instance

    configurationChanged = pyqtSignal

    ##  Gets the metadata dictionaries of all intent profiles for a given
    #   configuration.
    #
    #   \param definition_id: ID of the printer.
    #   \return A list of metadata dictionaries matching the search criteria, or
    #   an empty list if nothing was found.
    def intentMetadatas(self, definition_id: str, nozzle_name: str, material_id: str) -> List[Dict[str, Any]]:
        registry = ContainerRegistry.getInstance()
        return registry.findContainersMetadata(definition = definition_id, variant = nozzle_name, material_id = material_id)

    ##
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
    def currentAvailableIntents(self) -> List[Tuple[str, str]]:
        final_intent_ids = {metadata["id"] for metadata in ContainerRegistry.getInstance().findContainersMetadata(type = "intent", definition = current_definition_id)} #All intents that match the global stack.
        for extruder in all_extruders:
            extruder_intent_ids = {metadata["id"] for metadata in self.intentMetadatas(current_definition_id, extruder_nozzle_id, extruder_material_id)}
            final_intent_ids = final_intent_ids.intersection(extruder_intent_ids)

        result = set()
        for intent_id in final_intent_ids:
            intent = ContainerRegistry.getInstance().findContainers(id = intent_id)[0]
            result.add((intent.getMetaDataEntry("intent_category"), intent.getMetaDataEntry("quality_type")))
        return list(result)

    ##  List of intent categories to be displayed in the interface.
    @pyqtProperty("QVariantList", notify = configurationChanged)
    def currentAvailableIntentCategories(self) -> List[str]:
        final_intent_categories = {metadata["intent_category"] for metadata in ContainerRegistry.getInstance().findContainersMetadata(type = "intent", definition = current_definition_id)}
        for extruder in all_extruders:
            final_intent_categories = final_intent_categories.intersection(self.intentCategories())
        return list(final_intent_categories)

    def defaultIntent(self) -> Tuple[str, str]:
        default_quality_type = QualityManager.getInstance().getDefaultQualityType().quality_type
        for intent in self.currentAvailableIntents():
            if intent.getMetaDataEntry("intent_category") == "default" and intent.getMetaDataEntry("quality_type") == default_quality_type:
                return intent
        else: #Fallback: Preferred quality type is not available for default category.
            for intent in self.currentAvailableIntents():
                if intent.getMetaDataEntry("intent_category") == "default":
                    return intent
            else: #Fallback: No default category.
                if self.currentAvailableIntents():
                    return self.currentAvailableIntents()[0]
                else:
                    return CuraApplication.empty_intent_container

    def selectIntent(self, intent_category, quality_type):
        for extruder in all_extruders:
            extruder_stack.intent = ContainerRegistry.getInstance().findContainers(type = "intent", definition = current_definition_id, variant = extruder_nozzle_id, material = extruder_material_id)[0]
            extruder_stack.quality = ContainerRegistry.getInstance().findContainers(type = "quality", quality_type = quality_type)

    def selectDefaultIntent(self) -> None:
        category, quality_type = self.defaultIntent()
        self.selectIntent(category, quality_type)