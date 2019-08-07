# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING

from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.Interfaces import ContainerInterface
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
        container_registry = ContainerRegistry.getInstance()
        self.variant_name = container_registry.findContainersMetadata(id = container_id)[0]["name"]  # Store our own name so that we can filter more easily.
        container_registry.containerAdded.connect(self._materialAdded)
        self._loadAll()

    ##  (Re)loads all materials under this variant.
    def _loadAll(self):
        container_registry = ContainerRegistry.getInstance()
        # Find all the materials for this variant's name.
        if not self.machine.has_machine_materials:  # Printer has no specific materials. Look for all fdmprinter materials.
            materials = container_registry.findInstanceContainersMetadata(type = "material", definition = "fdmprinter")  # These are ONLY the base materials.
        else:  # Printer has its own material profiles. Look for material profiles with this printer's definition.
            all_materials = container_registry.findInstanceContainersMetadata(type = "material", definition = "fdmprinter")
            printer_specific_materials = container_registry.findInstanceContainersMetadata(type = "material", definition = self.machine.container_id)
            variant_specific_materials = container_registry.findInstanceContainersMetadata(type = "material", definition = self.machine.container_id, variant = self.variant_name)
            materials_per_base_file = {material["base_file"]: material for material in all_materials}
            materials_per_base_file.update({material["base_file"]: material for material in printer_specific_materials})  # Printer-specific profiles override global ones.
            materials_per_base_file.update({material["base_file"]: material for material in variant_specific_materials})  # Variant-specific profiles override all of those.
            materials = materials_per_base_file.values()

        for excluded_material in self.machine.exclude_materials:
            if excluded_material in materials:
                del materials[excluded_material]

        for material in materials:
            base_file = material["base_file"]
            if base_file not in self.materials:
                self.materials[base_file] = MaterialNode(material["id"], variant = self)

    ##  When a material gets added to the set of profiles, we need to update our
    #   tree here.
    def _materialAdded(self, container: ContainerInterface):
        if container.getMetaDataEntry("type") != "material":
            return  # Not interested.
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

        self.materials[base_file] = MaterialNode(container.getId(), variant = self)