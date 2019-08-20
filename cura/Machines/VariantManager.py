# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from collections import OrderedDict
from typing import Optional, TYPE_CHECKING, Dict

from UM.ConfigurationErrorMessage import ConfigurationErrorMessage
from UM.Decorators import deprecated
from UM.Logger import Logger
from UM.Util import parseBool

from cura.Machines.ContainerNode import ContainerNode
from cura.Machines.VariantType import VariantType, ALL_VARIANT_TYPES
from cura.Settings.CuraContainerRegistry import CuraContainerRegistry
from cura.Settings.GlobalStack import GlobalStack

if TYPE_CHECKING:
    from UM.Settings.DefinitionContainer import DefinitionContainer


#
# VariantManager is THE place to look for a specific variant. It maintains two variant lookup tables with the following
# structure:
#
#   [machine_definition_id] ->  [variant_type]  -> [variant_name]   -> ContainerNode(metadata / container)
# Example:   "ultimaker3"   ->    "buildplate"  ->   "Glass" (if present)  -> ContainerNode
#                                               ->    ...
#                           ->    "nozzle"      ->   "AA 0.4"
#                                               ->   "BB 0.8"
#                                               ->    ...
#
#   [machine_definition_id] -> [machine_buildplate_type] -> ContainerNode(metadata / container)
# Example:   "ultimaker3"   -> "glass" (this is different from the variant name) -> ContainerNode
#
# Note that the "container" field is not loaded in the beginning because it would defeat the purpose of lazy-loading.
# A container is loaded when getVariant() is called to load a variant InstanceContainer.
#
class VariantManager:
    __instance = None

    @classmethod
    @deprecated("Use the ContainerTree structure instead.", since = "4.3")
    def getInstance(cls) -> "VariantManager":
        if cls.__instance is None:
            cls.__instance = VariantManager()
        return cls.__instance

    def __init__(self) -> None:
        self._machine_to_variant_dict_map = dict()  # type: Dict[str, Dict["VariantType", Dict[str, ContainerNode]]]
        self._machine_to_buildplate_dict_map = dict() # type: Dict[str, Dict[str, ContainerNode]]

        self._exclude_variant_id_list = ["empty_variant"]

    #
    # Initializes the VariantManager including:
    #  - initializing the variant lookup table based on the metadata in ContainerRegistry.
    #
    def initialize(self) -> None:
        self._machine_to_variant_dict_map = OrderedDict()
        self._machine_to_buildplate_dict_map = OrderedDict()

        # Cache all variants from the container registry to a variant map for better searching and organization.
        container_registry = CuraContainerRegistry.getInstance
        variant_metadata_list = container_registry.findContainersMetadata(type = "variant")
        for variant_metadata in variant_metadata_list:
            if variant_metadata["id"] in self._exclude_variant_id_list:
                Logger.log("d", "Exclude variant [%s]", variant_metadata["id"])
                continue

            variant_name = variant_metadata["name"]
            variant_definition = variant_metadata["definition"]
            if variant_definition not in self._machine_to_variant_dict_map:
                self._machine_to_variant_dict_map[variant_definition] = OrderedDict()
                for variant_type in ALL_VARIANT_TYPES:
                    self._machine_to_variant_dict_map[variant_definition][variant_type] = dict()

            try:
                variant_type = variant_metadata["hardware_type"]
            except KeyError:
                Logger.log("w", "Variant %s does not specify a hardware_type; assuming 'nozzle'", variant_metadata["id"])
                variant_type = VariantType.NOZZLE
            variant_type = VariantType(variant_type)
            variant_dict = self._machine_to_variant_dict_map[variant_definition][variant_type]
            if variant_name in variant_dict:
                # ERROR: duplicated variant name.
                ConfigurationErrorMessage.getInstance().addFaultyContainers(variant_metadata["id"])
                continue #Then ignore this variant. This now chooses one of the two variants arbitrarily and deletes the other one! No guarantees!

            variant_dict[variant_name] = ContainerNode(metadata = variant_metadata)

            # If the variant is a buildplate then fill also the buildplate map
            if variant_type == VariantType.BUILD_PLATE:
                if variant_definition not in self._machine_to_buildplate_dict_map:
                    self._machine_to_buildplate_dict_map[variant_definition] = OrderedDict()

                try:
                    variant_container = container_registry.findContainers(type = "variant", id = variant_metadata["id"])[0]
                except IndexError as e:
                    # It still needs to break, but we want to know what variant ID made it break.
                    msg = "Unable to find build plate variant with the id [%s]" % variant_metadata["id"]
                    Logger.logException("e", msg)
                    raise IndexError(msg)

                buildplate_type = variant_container.getProperty("machine_buildplate_type", "value")
                if buildplate_type not in self._machine_to_buildplate_dict_map[variant_definition]:
                    self._machine_to_variant_dict_map[variant_definition][buildplate_type] = dict()

                self._machine_to_buildplate_dict_map[variant_definition][buildplate_type] = variant_dict[variant_name]

    #
    # Gets the variant InstanceContainer with the given information.
    # Almost the same as getVariantMetadata() except that this returns an InstanceContainer if present.
    #
    def getVariantNode(self, machine_definition_id: str, variant_name: str,
                       variant_type: Optional["VariantType"] = None) -> Optional["ContainerNode"]:
        if variant_type is None:
            variant_node = None
            variant_type_dict = self._machine_to_variant_dict_map.get("machine_definition_id", {})
            for variant_dict in variant_type_dict.values():
                if variant_name in variant_dict:
                    variant_node = variant_dict[variant_name]
                    break
            return variant_node

        return self._machine_to_variant_dict_map.get(machine_definition_id, {}).get(variant_type, {}).get(variant_name)

    def getVariantNodes(self, machine: "GlobalStack", variant_type: "VariantType") -> Dict[str, ContainerNode]:
        machine_definition_id = machine.definition.getId()
        return self._machine_to_variant_dict_map.get(machine_definition_id, {}).get(variant_type, {})

    #
    # Gets the default variant for the given machine definition.
    # If the optional GlobalStack is given, the metadata information will be fetched from the GlobalStack instead of
    # the DefinitionContainer. Because for machines such as UM2, you can enable Olsson Block, which will set
    # "has_variants" to True in the GlobalStack. In those cases, we need to fetch metadata from the GlobalStack or
    # it may not be correct.
    #
    def getDefaultVariantNode(self, machine_definition: "DefinitionContainer",
                              variant_type: "VariantType",
                              global_stack: Optional["GlobalStack"] = None) -> Optional["ContainerNode"]:
        machine_definition_id = machine_definition.getId()
        container_for_metadata_fetching = global_stack if global_stack is not None else machine_definition

        preferred_variant_name = None
        if variant_type == VariantType.BUILD_PLATE:
            if parseBool(container_for_metadata_fetching.getMetaDataEntry("has_variant_buildplates", False)):
                preferred_variant_name = container_for_metadata_fetching.getMetaDataEntry("preferred_variant_buildplate_name")
        else:
            if parseBool(container_for_metadata_fetching.getMetaDataEntry("has_variants", False)):
                preferred_variant_name = container_for_metadata_fetching.getMetaDataEntry("preferred_variant_name")

        node = None
        if preferred_variant_name:
            node = self.getVariantNode(machine_definition_id, preferred_variant_name, variant_type)
        return node

    def getBuildplateVariantNode(self, machine_definition_id: str, buildplate_type: str) -> Optional["ContainerNode"]:
        if machine_definition_id in self._machine_to_buildplate_dict_map:
            return self._machine_to_buildplate_dict_map[machine_definition_id].get(buildplate_type)
        return None
