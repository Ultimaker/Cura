# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Dict, List

from UM.Logger import Logger
from UM.Signal import Signal
from UM.Util import parseBool
from UM.Settings.ContainerRegistry import ContainerRegistry  # To find all the variants for this machine.
from cura.Machines.ContainerNode import ContainerNode
from cura.Machines.QualityChangesGroup import QualityChangesGroup  # To construct groups of quality changes profiles that belong together.
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
        self.materialsChanged = Signal()  # Emitted when one of the materials underneath this machine has been changed.

        container_registry = ContainerRegistry.getInstance()
        try:
            my_metadata = container_registry.findContainersMetadata(id = container_id)[0]
        except IndexError:
            Logger.log("Unable to find metadata for container %s", container_id)
            my_metadata = {}
        # Some of the metadata is cached upon construction here.
        # ONLY DO THAT FOR METADATA THAT DOESN'T CHANGE DURING RUNTIME!
        # Otherwise you need to keep it up-to-date during runtime.
        self.has_materials = parseBool(my_metadata.get("has_materials", "true"))
        self.has_variants = parseBool(my_metadata.get("has_variants", "false"))
        self.has_machine_materials = parseBool(my_metadata.get("has_machine_materials", "false"))
        self.has_machine_quality = parseBool(my_metadata.get("has_machine_quality", "false"))
        self.quality_definition = my_metadata.get("quality_definition", container_id)
        self.exclude_materials = my_metadata.get("exclude_materials", [])
        self.preferred_variant_name = my_metadata.get("preferred_variant_name", "")
        self.preferred_material = my_metadata.get("preferred_material", "")
        self.preferred_quality_type = my_metadata.get("preferred_quality_type", "")

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
            quality_groups[quality_type] = QualityGroup(name = global_quality_node.container.getMetaDataEntry("name", "Unnamed profile"), quality_type = quality_type)
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

    ##  Returns all of the quality changes groups available to this printer.
    #
    #   The quality changes groups store which quality type and intent category
    #   they were made for, but not which material and nozzle. Instead for the
    #   quality type and intent category, the quality changes will always be
    #   available but change the quality type and intent category when
    #   activated.
    #
    #   The quality changes group does depend on the printer: Which quality
    #   definition is used.
    #
    #   The quality changes groups that are available do depend on the quality
    #   types that are available, so it must still be known which extruders are
    #   enabled and which materials and variants are loaded in them. This allows
    #   setting the correct is_available flag.
    #   \param variant_names The names of the variants loaded in each extruder.
    #   \param material_bases The base file names of the materials loaded in
    #   each extruder.
    #   \param extruder_enabled For each extruder whether or not they are
    #   enabled.
    #   \return List of all quality changes groups for the printer.
    def getQualityChangesGroups(self, variant_names: List[str], material_bases: List[str], extruder_enabled: List[bool]) -> List[QualityChangesGroup]:
        machine_quality_changes = ContainerRegistry.getInstance().findContainersMetadata(type = "quality_changes", definition = self.quality_definition)  # All quality changes for each extruder.

        groups_by_name = {}  # Group quality changes profiles by their display name. The display name must be unique for quality changes. This finds profiles that belong together in a group.
        for quality_changes in machine_quality_changes:
            name = quality_changes["name"]
            if name not in groups_by_name:
                groups_by_name[name] = QualityChangesGroup(name, quality_type = quality_changes["quality_type"], intent_category = quality_changes.get("intent_category", "default"))
            if "position" in quality_changes:  # An extruder profile.
                groups_by_name[name].metadata_per_extruder[int(quality_changes["position"])] = quality_changes
            else:  # Global profile.
                groups_by_name[name].metadata_for_global = quality_changes

        quality_groups = self.getQualityGroups(variant_names, material_bases, extruder_enabled)
        for quality_changes_group in groups_by_name.values():
            if quality_changes_group.quality_type not in quality_groups:
                quality_changes_group.is_available = False
            else:
                # Quality changes group is available iff the quality group it depends on is available. Irrespective of whether the intent category is available.
                quality_changes_group.is_available = quality_groups[quality_changes_group.quality_type].is_available

        return list(groups_by_name.values())

    ##  (Re)loads all variants under this printer.
    def _loadAll(self):
        container_registry = ContainerRegistry.getInstance()
        if not self.has_variants:
            self.variants["empty"] = VariantNode("empty_variant", machine = self)
        else:
            # Find all the variants for this definition ID.
            variants = container_registry.findInstanceContainersMetadata(type = "variant", definition = self.container_id, hardware_type = "nozzle")
            for variant in variants:
                variant_name = variant["name"]
                if variant_name not in self.variants:
                    self.variants[variant_name] = VariantNode(variant["id"], machine = self)
                    self.variants[variant_name].materialsChanged.connect(self.materialsChanged)
            if not self.variants:
                self.variants["empty"] = VariantNode("empty_variant", machine = self)

        # Find the global qualities for this printer.
        global_qualities = container_registry.findInstanceContainersMetadata(type = "quality", definition = self.quality_definition, global_quality = "True")  # First try specific to this printer.
        if len(global_qualities) == 0:  # This printer doesn't override the global qualities.
            global_qualities = container_registry.findInstanceContainersMetadata(type = "quality", definition = "fdmprinter", global_quality = "True")  # Otherwise pick the global global qualities.
        for global_quality in global_qualities:
            self.global_qualities[global_quality["quality_type"]] = QualityNode(global_quality["id"], parent = self)