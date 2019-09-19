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

        self._exclude_variant_id_list = ["empty_variant"]

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
