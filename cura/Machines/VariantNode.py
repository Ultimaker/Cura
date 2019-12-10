# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional, TYPE_CHECKING

from UM.Logger import Logger
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.Interfaces import ContainerInterface
from UM.Signal import Signal

from cura.Settings.cura_empty_instance_containers import empty_variant_container
from cura.Machines.ContainerNode import ContainerNode
from cura.Machines.MaterialNode import MaterialNode

import UM.FlameProfiler

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
        container_registry.containerRemoved.connect(self._materialRemoved)
        self._loadAll()

    ##  (Re)loads all materials under this variant.
    @UM.FlameProfiler.profile
    def _loadAll(self) -> None:
        container_registry = ContainerRegistry.getInstance()

        if not self.machine.has_materials:
            self.materials["empty_material"] = MaterialNode("empty_material", variant = self)
            return  # There should not be any materials loaded for this printer.

        # Find all the materials for this variant's name.
        else:  # Printer has its own material profiles. Look for material profiles with this printer's definition.
            base_materials = container_registry.findInstanceContainersMetadata(type = "material", definition = "fdmprinter")
            printer_specific_materials = container_registry.findInstanceContainersMetadata(type = "material", definition = self.machine.container_id, variant_name = None)
            variant_specific_materials = container_registry.findInstanceContainersMetadata(type = "material", definition = self.machine.container_id, variant_name = self.variant_name)  # If empty_variant, this won't return anything.
            materials_per_base_file = {material["base_file"]: material for material in base_materials}
            materials_per_base_file.update({material["base_file"]: material for material in printer_specific_materials})  # Printer-specific profiles override global ones.
            materials_per_base_file.update({material["base_file"]: material for material in variant_specific_materials})  # Variant-specific profiles override all of those.
            materials = list(materials_per_base_file.values())

        # Filter materials based on the exclude_materials property.
        filtered_materials = [material for material in materials if material["id"] not in self.machine.exclude_materials]

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
    #   If the preferred material is not available, an arbitrary material is
    #   returned. If there is a configuration mistake (like a typo in the
    #   preferred material) this returns a random available material. If there
    #   are no available materials, this will return the empty material node.
    #   \param approximate_diameter The desired approximate diameter of the
    #   material.
    #   \return The node for the preferred material, or any arbitrary material
    #   if there is no match.
    def preferredMaterial(self, approximate_diameter: int) -> MaterialNode:
        for base_material, material_node in self.materials.items():
            if self.machine.preferred_material == base_material and approximate_diameter == int(material_node.getMetaDataEntry("approximate_diameter")):
                return material_node
            
        # First fallback: Check if we should be checking for the 175 variant.
        if approximate_diameter == 2:
            preferred_material = self.machine.preferred_material + "_175"
            for base_material, material_node in self.materials.items():
                if preferred_material == base_material and approximate_diameter == int(material_node.getMetaDataEntry("approximate_diameter")):
                    return material_node
        
        # Second fallback: Choose any material with matching diameter.
        for material_node in self.materials.values():
            if material_node.getMetaDataEntry("approximate_diameter") and approximate_diameter == int(material_node.getMetaDataEntry("approximate_diameter")):
                Logger.log("w", "Could not find preferred material %s, falling back to whatever works", self.machine.preferred_material)
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
    @UM.FlameProfiler.profile
    def _materialAdded(self, container: ContainerInterface) -> None:
        if container.getMetaDataEntry("type") != "material":
            return  # Not interested.
        if not ContainerRegistry.getInstance().findContainersMetadata(id = container.getId()):
            # CURA-6889
            # containerAdded and removed signals may be triggered in the next event cycle. If a container gets added
            # and removed in the same event cycle, in the next cycle, the connections should just ignore the signals.
            # The check here makes sure that the container in the signal still exists.
            Logger.log("d", "Got container added signal for container [%s] but it no longer exists, do nothing.",
                       container.getId())
            return
        if not self.machine.has_materials:
            return  # We won't add any materials.
        material_definition = container.getMetaDataEntry("definition")

        base_file = container.getMetaDataEntry("base_file")
        if base_file in self.machine.exclude_materials:
            return  # Material is forbidden for this printer.
        if base_file not in self.materials:  # Completely new base file. Always better than not having a file as long as it matches our set-up.
            if material_definition != "fdmprinter" and material_definition != self.machine.container_id:
                return
            material_variant = container.getMetaDataEntry("variant_name")
            if material_variant is not None and material_variant != self.variant_name:
                return
        else:  # We already have this base profile. Replace the base profile if the new one is more specific.
            new_definition = container.getMetaDataEntry("definition")
            if new_definition == "fdmprinter":
                return  # Just as unspecific or worse.
            material_variant = container.getMetaDataEntry("variant_name")
            if new_definition != self.machine.container_id or material_variant != self.variant_name:
                return  # Doesn't match this set-up.
            original_metadata = ContainerRegistry.getInstance().findContainersMetadata(id = self.materials[base_file].container_id)[0]
            if "variant_name" in original_metadata or material_variant is None:
                return  # Original was already specific or just as unspecific as the new one.

        if "empty_material" in self.materials:
            del self.materials["empty_material"]
        self.materials[base_file] = MaterialNode(container.getId(), variant = self)
        self.materials[base_file].materialChanged.connect(self.materialsChanged)
        self.materialsChanged.emit(self.materials[base_file])

    @UM.FlameProfiler.profile
    def _materialRemoved(self, container: ContainerInterface) -> None:
        if container.getMetaDataEntry("type") != "material":
            return  # Only interested in materials.
        base_file = container.getMetaDataEntry("base_file")
        if base_file not in self.materials:
            return  # We don't track this material anyway. No need to remove it.

        original_node = self.materials[base_file]
        del self.materials[base_file]
        self.materialsChanged.emit(original_node)

        # Now a different material from the same base file may have been hidden because it was not as specific as the one we deleted.
        # Search for any submaterials from that base file that are still left.
        materials_same_base_file = ContainerRegistry.getInstance().findContainersMetadata(base_file = base_file)
        if materials_same_base_file:
            most_specific_submaterial = None
            for submaterial in materials_same_base_file:
                if submaterial["definition"] == self.machine.container_id:
                    if submaterial.get("variant_name", "empty") == self.variant_name:
                        most_specific_submaterial = submaterial
                        break  # most specific match possible
                    if submaterial.get("variant_name", "empty") == "empty":
                        most_specific_submaterial = submaterial

            if most_specific_submaterial is None:
                Logger.log("w", "Material %s removed, but no suitable replacement found", base_file)
            else:
                Logger.log("i", "Material %s (%s) overridden by %s", base_file, self.variant_name, most_specific_submaterial.get("id"))
                self.materials[base_file] = MaterialNode(most_specific_submaterial["id"], variant = self)
                self.materialsChanged.emit(self.materials[base_file])

        if not self.materials:  # The last available material just got deleted and there is nothing with the same base file to replace it.
            self.materials["empty_material"] = MaterialNode("empty_material", variant = self)
            self.materialsChanged.emit(self.materials["empty_material"])