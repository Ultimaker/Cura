# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, TYPE_CHECKING

from UM.Logger import Logger
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.Interfaces import ContainerInterface
from UM.Signal import Signal
from cura.Machines.ContainerNode import ContainerNode
from cura.Machines.MaterialNode import MaterialNode

if TYPE_CHECKING:
    from typing import Dict
    from cura.Machines.MachineNode import MachineNode

##  This class represents an extruder variant in the container tree.
#
#   The subnodes of these nodes are materials.
#
#   This node contains materials with ALL filament diameters underneath it. The
#   tree of this variant is not specific to one global stack, so because the
#   list of materials can be different per stack depending on the compatible
#   material diameter setting, we cannot filter them here. Filtering must be
#   done in the model.
class VariantNode(ContainerNode):
    def __init__(self, container_id: str, machine: "MachineNode") -> None:
        super().__init__(container_id)
        self.machine = machine
        self.materials = {}  # type: Dict[str, MaterialNode]  # Mapping material base files to their nodes.
        self.materialsChanged = Signal()

        container_registry = ContainerRegistry.getInstance()
        self.variant_name = container_registry.findContainersMetadata(id = container_id)[0]["name"]  # Store our own name so that we can filter more easily.
        container_registry.containerAdded.connect(self._materialAdded)
        self._loadAll()

    ##  (Re)loads all materials under this variant.
    def _loadAll(self):
        container_registry = ContainerRegistry.getInstance()

        if not self.machine.has_materials:
            self.materials["empty_material"] = MaterialNode("empty_material", variant = self)
            return  # There should not be any materials loaded for this printer.

        # Find all the materials for this variant's name.
        if not self.machine.has_machine_materials:  # Printer has no specific materials. Look for all fdmprinter materials.
            materials = container_registry.findInstanceContainersMetadata(type = "material", definition = "fdmprinter")  # These are ONLY the base materials.
        else:  # Printer has its own material profiles. Look for material profiles with this printer's definition.
            all_materials = container_registry.findInstanceContainersMetadata(type = "material", definition = "fdmprinter")
            printer_specific_materials = container_registry.findInstanceContainersMetadata(type = "material", definition = self.machine.container_id)
            variant_specific_materials = container_registry.findInstanceContainersMetadata(type = "material", definition = self.machine.container_id, variant = self.variant_name)  # If empty_variant, this won't return anything.
            materials_per_base_file = {material["base_file"]: material for material in all_materials}
            materials_per_base_file.update({material["base_file"]: material for material in printer_specific_materials})  # Printer-specific profiles override global ones.
            materials_per_base_file.update({material["base_file"]: material for material in variant_specific_materials})  # Variant-specific profiles override all of those.
            materials = materials_per_base_file.values()

        filtered_materials = []
        for material in materials:
            if material["id"] not in self.machine.exclude_materials:
                filtered_materials.append(material)

        for material in filtered_materials:
            base_file = material["base_file"]
            if base_file not in self.materials:
                self.materials[base_file] = MaterialNode(material["id"], variant = self)
                self.materials[base_file].materialChanged.connect(self.materialsChanged)
        if not self.materials:
            self.materials["empty_material"] = MaterialNode("empty_material", variant = self)

    ##  Finds the preferred material for this printer with this nozzle in one of
    #   the extruders.
    #
    #   If there is no material here (because the printer has no materials or
    #   because there are no matching material profiles), None is returned.
    #   \param approximate_diameter The desired approximate diameter of the
    #   material.
    #   \return The node for the preferred material, or None if there is no
    #   match.
    def preferredMaterial(self, approximate_diameter) -> MaterialNode:
        for base_material, material_node in self.materials.items():
            if self.machine.preferred_material in base_material and approximate_diameter == int(material_node.getMetaDataEntry("approximate_diameter")):
                return material_node
        fallback = next(iter(self.materials.values()))  # Should only happen with empty material node.
        Logger.log("w", "Could not find preferred material {preferred_material} with diameter {diameter} for variant {variant_id}, falling back to {fallback}.".format(
            preferred_material = self.machine.preferred_material,
            diameter = approximate_diameter,
            variant_id = self.container_id,
            fallback = fallback.container_id
        ))
        return fallback

    ##  When a material gets added to the set of profiles, we need to update our
    #   tree here.
    def _materialAdded(self, container: ContainerInterface):
        if container.getMetaDataEntry("type") != "material":
            return  # Not interested.
        if not self.machine.has_materials:
            return  # We won't add any materials.
        material_definition = container.getMetaDataEntry("definition")
        if not self.machine.has_machine_materials:
            if material_definition != "fdmprinter":
                return

        base_file = container.getMetaDataEntry("base_file")
        if base_file in self.machine.exclude_materials:
            return  # Material is forbidden for this printer.
        if base_file not in self.materials:  # Completely new base file. Always better than not having a file as long as it matches our set-up.
            if material_definition != "fdmprinter" and material_definition != self.machine.container_id:
                return
            material_variant = container.getMetaDataEntry("variant", "empty")
            if material_variant != "empty" and material_variant != self.variant_name:
                return
        else:  # We already have this base profile. Replace the base profile if the new one is more specific.
            new_definition = container.getMetaDataEntry("definition")
            if new_definition == "fdmprinter":
                return  # Just as unspecific or worse.
            if new_definition != self.machine.container_id:
                return  # Doesn't match this set-up.
            original_metadata = ContainerRegistry.getInstance().findContainersMetadata(id = self.materials[base_file].container_id)[0]
            original_variant = original_metadata.get("variant", "empty")
            if original_variant != "empty" or container.getMetaDataEntry("variant", "empty") == "empty":
                return  # Original was already specific or just as unspecific as the new one.

        if "empty_material" in self.materials:
            del self.materials["empty_material"]
        self.materials[base_file] = MaterialNode(container.getId(), variant = self)
        self.materials[base_file].materialChanged.connect(self.materialsChanged)