# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Dict, List

from UM.Logger import Logger
from UM.Util import parseBool
from UM.Settings.ContainerRegistry import ContainerRegistry  # To find all the variants for this machine.
from UM.Settings.Interfaces import ContainerInterface
from cura.Machines.ContainerNode import ContainerNode
from cura.Machines.QualityGroup import QualityGroup  # To construct groups of quality profiles that belong together.
from cura.Machines.QualityNode import QualityNode
from cura.Machines.VariantNode import VariantNode

##  This class represents a machine in the container tree.
#
#   The subnodes of these nodes are variants.
class MachineNode(ContainerNode):
    def __init__(self, container_id: str) -> None:
        super().__init__(container_id)
        self.variants = {}  # type: Dict[str, VariantNode] # Mapping variant names to their nodes.
        self.global_qualities = {}  # type: Dict[str, QualityNode] # Mapping quality types to the global quality for those types.
        container_registry = ContainerRegistry.getInstance()
        try:
            my_metadata = container_registry.findContainersMetadata(id = container_id)[0]
        except IndexError:
            Logger.log("Unable to find metadata for container %s", container_id)
            my_metadata = {}
        # Some of the metadata is cached upon construction here.
        # ONLY DO THAT FOR METADATA THAT DOESN'T CHANGE DURING RUNTIME!
        # Otherwise you need to keep it up-to-date during runtime.
        self.has_machine_materials = parseBool(my_metadata.get("has_machine_materials", "false"))
        self.has_machine_quality = parseBool(my_metadata.get("has_machine_quality", "false"))
        self.quality_definition = my_metadata.get("quality_definition", container_id)
        self.exclude_materials = my_metadata.get("exclude_materials", [])
        self.preferred_variant_name = my_metadata.get("preferred_variant_name", "")
        self.preferred_quality_type = my_metadata.get("preferred_quality_type", "")

        container_registry.containerAdded.connect(self._variantAdded)
        self._loadAll()

    ##  Get the available quality groups for this machine.
    #
    #   This returns all quality groups, regardless of whether they are
    #   available to the combination of extruders or not. On the resulting
    #   quality groups, the is_available property is set to indicate whether the
    #   quality group can be selected according to the combination of extruders
    #   in the parameters.
    #   \param variant_names The names of the variants loaded in each extruder.
    #   \param material_bases The base file names of the materials loaded in
    #   each extruder.
    #   \param extruder_enabled Whether or not the extruders are enabled. This
    #   allows the function to set the is_available properly.
    #   \return For each available quality type, a QualityGroup instance.
    def getQualityGroups(self, variant_names: List[str], material_bases: List[str], extruder_enabled: List[bool]) -> Dict[str, QualityGroup]:
        if len(variant_names) != len(material_bases) or len(variant_names) != len(extruder_enabled):
            Logger.log("e", "The number of extruders in the list of variants (" + str(len(variant_names)) + ") is not equal to the number of extruders in the list of materials (" + str(len(material_bases)) + ") or the list of enabled extruders (" + str(len(extruder_enabled)) + ").")
            return {}
        # For each extruder, find which quality profiles are available. Later we'll intersect the quality types.
        qualities_per_type_per_extruder = [{} for _ in range(len(variant_names))]  # type: List[Dict[str, QualityNode]]
        for extruder_nr, variant_name in enumerate(variant_names):
            if not extruder_enabled[extruder_nr]:
                continue  # No qualities are available in this extruder. It'll get skipped when calculating the available quality types.
            material_base = material_bases[extruder_nr]
            if variant_name not in self.variants or material_base not in self.variants[variant_name].materials:
                # The printer has no variant/material-specific quality profiles. Use the global quality profiles.
                qualities_per_type_per_extruder[extruder_nr] = self.global_qualities
            else:
                # Use the actually specialised quality profiles.
                qualities_per_type_per_extruder[extruder_nr] = self.variants[variant_name].materials[material_base].qualities

        # Create the quality group for each available type.
        quality_groups = {}
        for quality_type, global_quality_node in self.global_qualities.items():
            quality_groups[quality_type] = QualityGroup(name = global_quality_node.getMetaDataEntry("name", "Unnamed profile"), quality_type = quality_type)
            quality_groups[quality_type].node_for_global = global_quality_node
            for extruder, qualities_per_type in qualities_per_type_per_extruder:
                quality_groups[quality_type].nodes_for_extruders[extruder] = qualities_per_type[quality_type]

        available_quality_types = set(quality_groups.keys())
        for extruder_nr, qualities_per_type in enumerate(qualities_per_type_per_extruder):
            if not extruder_enabled[extruder_nr]:
                continue
            available_quality_types.intersection_update(qualities_per_type.keys())
        for quality_type in available_quality_types:
            quality_groups[quality_type].is_available = True
        return quality_groups

    ##  (Re)loads all variants under this printer.
    def _loadAll(self):
        # Find all the variants for this definition ID.
        container_registry = ContainerRegistry.getInstance()
        variants = container_registry.findInstanceContainersMetadata(type = "variant", definition = self.container_id, hardware_type = "nozzle")
        for variant in variants:
            variant_name = variant["name"]
            if variant_name not in self.variants:
                self.variants[variant_name] = VariantNode(variant["id"], machine = self)

        # Find the global qualities for this printer.
        global_qualities = container_registry.findInstanceContainersMetadata(type = "quality", definition = self.container_id, global_quality = True)  # First try specific to this printer.
        if len(global_qualities) == 0:  # This printer doesn't override the global qualities.
            global_qualities = container_registry.findInstanceContainersMetadata(type = "quality", definition = "fdmprinter", global_quality = True)  # Otherwise pick the global global qualities.
        for global_quality in global_qualities:
            self.global_qualities[global_quality["quality_type"]] = QualityNode(global_quality["id"], parent = self)

    ##  When a variant gets added to the set of profiles, we need to update our
    #   tree here.
    def _variantAdded(self, container: ContainerInterface):
        if container.getMetaDataEntry("type") != "variant":
            return  # Not interested.
        name = container.getMetaDataEntry("name")
        if name in self.variants:
            return  # Already have this one.
        if container.getMetaDataEntry("hardware_type") != "nozzle":
            return  # Only want nozzles in my tree.
        if container.getMetaDataEntry("definition") != self.container_id:
            return  # Not a nozzle that fits in my machine.

        self.variants[name] = VariantNode(container.getId(), machine = self)