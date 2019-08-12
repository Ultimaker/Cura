# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING

from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.Interfaces import ContainerInterface
from cura.Machines.ContainerNode import ContainerNode
from cura.Machines.QualityNode import QualityNode

if TYPE_CHECKING:
    from typing import Dict
    from cura.Machines.VariantNode import VariantNode

##  Represents a material in the container tree.
#
#   Its subcontainers are quality profiles.
class MaterialNode(ContainerNode):
    def __init__(self, container_id, variant: "VariantNode") -> None:
        super().__init__(container_id)
        self.variant = variant
        self.qualities = {}  # type: Dict[str, QualityNode] # Mapping container IDs to quality profiles.
        container_registry = ContainerRegistry.getInstance()
        my_metadata = container_registry.findContainersMetadata(id = container_id)[0]
        self.base_file = my_metadata["base_file"]
        container_registry.containerAdded.connect(self._qualityAdded)
        self._loadAll()

    def _loadAll(self) -> None:
        container_registry = ContainerRegistry.getInstance()
        # Find all quality profiles that fit on this material.
        if not self.variant.machine.has_machine_quality:  # Need to find the global qualities.
            qualities = container_registry.findInstanceContainersMetadata(type = "quality", definition = "fdmprinter")
        else:
            # Need to find the qualities that specify a material profile with the same material type.
            my_metadata = container_registry.findInstanceContainersMetadata(id = self.container_id)[0]
            my_material_type = my_metadata.get("material")
            qualities = []
            qualities_any_material = container_registry.findInstanceContainersMetadata(type = "quality", definition = self.variant.machine.quality_definition, variant = self.variant.variant_name)
            for material_metadata in container_registry.findInstanceContainersMetadata(type = "material", material = my_material_type):
                qualities.extend((quality for quality in qualities_any_material if quality["material"] == material_metadata["id"]))
            if not qualities:  # No quality profiles found. Go by GUID then.
                my_guid = my_metadata.get("material")
                for material_metadata in container_registry.findInstanceContainersMetadata(type = "material", guid = my_guid):
                    qualities.extend((quality for quality in qualities_any_material if quality["material"] == material_metadata["id"]))

        for quality in qualities:
            quality_id = quality["id"]
            if quality_id not in self.qualities:
                self.qualities[quality_id] = QualityNode(quality_id, parent = self)

    def _qualityAdded(self, container: ContainerInterface) -> None:
        if container.getMetaDataEntry("type") != "quality":
            return  # Not interested.
        if not self.variant.machine.has_machine_quality:
            if container.getMetaDataEntry("definition") != "fdmprinter":
                return  # Only want global qualities.
        else:
            if container.getMetaDataEntry("definition") != self.variant.machine.quality_definition:
                return  # Doesn't match the machine.
            if container.getMetaDataEntry("variant") != self.variant.variant_name:
                return  # Doesn't match the variant.
            # Detect if we're falling back to matching via GUID.
            # If so, we might need to erase the current list and put just this one in (i.e. no longer use the fallback).
            container_registry = ContainerRegistry.getInstance()
            my_metadata = container_registry.findInstanceContainersMetadata(id = self.container_id)[0]
            my_material_type = my_metadata.get("material")
            allowed_material_ids = {metadata["id"] for metadata in container_registry.findInstanceContainersMetadata(type = "material", material = my_material_type)}
            is_fallback_guid = len(self.qualities) == 0 or next(iter(self.qualities.values())).getMetaDataEntry("material") not in allowed_material_ids  # Select any quality profile; if the material is not matching by material type, we've been falling back to GUID.

            if is_fallback_guid and container.getMetaDataEntry("material") in allowed_material_ids:  # So far we needed the fallback, but no longer!
                self.qualities.clear()
            else:
                if not is_fallback_guid:
                    if container.getMetaDataEntry("material") not in allowed_material_ids:
                        return  # Doesn't match the material type.
                else:
                    my_material_guid = my_metadata["guid"]
                    allowed_material_ids = {metadata["id"] for metadata in container_registry.findInstanceContainersMetadata(type = "material", guid = my_material_guid)}
                    if container.getMetaDataEntry("material") not in allowed_material_ids:
                        return  # Doesn't match the material GUID.

        quality_id = container.getId()
        self.qualities[quality_id] = QualityNode(quality_id, parent = self)