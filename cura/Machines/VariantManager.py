from typing import Optional

from UM.Logger import Logger
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.InstanceContainer import InstanceContainer

from cura.Machines.ContainerNode import ContainerNode
from cura.Settings.GlobalStack import GlobalStack


class VariantType:
    BUILD_PLATE = "buildplate"
    NOZZLE = "nozzle"


ALL_VARIANT_TYPES = (VariantType.BUILD_PLATE, VariantType.NOZZLE)


#
# VariantManager is THE place to look for a specific variant. It maintains a variant lookup table with the following
# structure:
#
#   [machine_definition_id] ->  [variant_type]  -> [variant_name]   -> ContainerNode(metadata / container)
# Example:   "ultimaker3"   ->    "buildplate"  ->   "Glass" (if present)  -> ContainerNode
#                                               ->    ...
#                           ->    "nozzle"      ->   "AA 0.4"
#                                               ->   "BB 0.8"
#                                               ->    ...
#
# Note that the "container" field is not loaded in the beginning because it would defeat the purpose of lazy-loading.
# A container is loaded when getVariant() is called to load a variant InstanceContainer.
#
class VariantManager:

    def __init__(self, container_registry):
        self._container_registry = container_registry  # type: ContainerRegistry

        self._machine_to_variant_dict_map = {}  # <machine_type> -> <variant_dict>

        self._exclude_variant_id_list = ["empty_variant"]

    #
    # Initializes the VariantManager including:
    #  - initializing the variant lookup table based on the metadata in ContainerRegistry.
    #
    def initialize(self):
        # Cache all variants from the container registry to a variant map for better searching and organization.
        variant_metadata_list = self._container_registry.findContainersMetadata(type = "variant")
        for variant_metadata in variant_metadata_list:
            if variant_metadata["id"] in self._exclude_variant_id_list:
                Logger.log("d", "Exclude variant [%s]", variant_metadata["id"])
                continue

            variant_name = variant_metadata["name"]
            variant_definition = variant_metadata["definition"]
            if variant_definition not in self._machine_to_variant_dict_map:
                self._machine_to_variant_dict_map[variant_definition] = {}
                #for variant_type in ALL_VARIANT_TYPES:
                #    self._machine_to_variant_dict_map[variant_definition][variant_type] = {}

            variant_type = variant_metadata["hardware_type"]
            #variant_dict = self._machine_to_variant_dict_map[variant_definition][variant_type]
            variant_dict = self._machine_to_variant_dict_map[variant_definition]
            if variant_name in variant_dict:
                # ERROR: duplicated variant name.
                raise RuntimeError("Found duplicated variant name [%s], type [%s] for machine [%s]" %
                                   (variant_name, variant_type, variant_definition))

            variant_dict[variant_name] = ContainerNode(metadata = variant_metadata)

    #
    # Gets the variant InstanceContainer with the given information.
    # Almost the same as getVariantMetadata() except that this returns an InstanceContainer if present.
    #
    def getVariant(self, machine_type_name: str, variant_name: str,
                   variant_type: Optional[str] = None) -> Optional["InstanceContainer"]:
        return self._machine_to_variant_dict_map[machine_type_name].get(variant_name)

    def getVariantNodes(self, machine: "GlobalStack"):
        machine_type_name = machine.definition.getId()
        return self._machine_to_variant_dict_map.get(machine_type_name)
