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
            qualities = container_registry.findInstanceContainersMetadata(type = "quality", definition = self.variant.machine.quality_definition, variant = self.variant.variant_name, material = self.base_file)

        for quality in qualities:
            quality_id = quality["id"]
            if quality_id not in self.qualities:
                self.qualities[quality_id] = QualityNode(quality_id, material = self)

    def _qualityAdded(self, container: ContainerInterface) -> None:
        if container.getMetaDataEntry("type") != "quality":
            return  # Not interested.
        if not self.variant.machine.has_machine_quality:
            if container.getMetaDataEntry("definition") != "fdmprinter":
                return  # Only want global qualities.
        else:
            if container.getMetaDataEntry("definition") != self.variant.machine.quality_definition or container.getMetaDataEntry("variant") != self.variant.variant_name or container.getMetaDataEntry("material") != self.base_file:
                return  # Doesn't match our configuration.

        quality_id = container.getId()
        self.qualities[quality_id] = QualityNode(quality_id, material = self)