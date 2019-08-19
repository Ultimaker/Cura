# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, TYPE_CHECKING

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
        self.material_type = my_metadata["material"]
        self.guid = my_metadata["GUID"]
        self._loadAll()
        container_registry.containerRemoved.connect(self._onRemoved)
        container_registry.containerMetaDataChanged(self._onMetadataChanged)

    def _loadAll(self) -> None:
        container_registry = ContainerRegistry.getInstance()
        # Find all quality profiles that fit on this material.
        if not self.variant.machine.has_machine_quality:  # Need to find the global qualities.
            qualities = container_registry.findInstanceContainersMetadata(type = "quality", definition = "fdmprinter")
        else:
            # Need to find the qualities that specify a material profile with the same material type.
            my_material_type = self.material_type
            qualities = []
            qualities_any_material = container_registry.findInstanceContainersMetadata(type = "quality", definition = self.variant.machine.quality_definition, variant = self.variant.variant_name)
            for material_metadata in container_registry.findInstanceContainersMetadata(type = "material", material = my_material_type):
                qualities.extend((quality for quality in qualities_any_material if quality["material"] == material_metadata["id"]))
            if not qualities:  # No quality profiles found. Go by GUID then.
                my_guid = self.guid
                for material_metadata in container_registry.findInstanceContainersMetadata(type = "material", guid = my_guid):
                    qualities.extend((quality for quality in qualities_any_material if quality["material"] == material_metadata["id"]))

        for quality in qualities:
            quality_id = quality["id"]
            if quality_id not in self.qualities:
                self.qualities[quality_id] = QualityNode(quality_id, parent = self)

    ##  Triggered when any container is removed, but only handles it when the
    #   container is removed that this node represents.
    #   \param container The container that was allegedly removed.
    def _onRemoved(self, container: ContainerInterface) -> None:
        if container.getId() == self.container_id:
            # Remove myself from my parent.
            if self.base_file in self.variant.materials:
                del self.variant.materials[self.base_file]

    ##  Triggered when any metadata changed in any container, but only handles
    #   it when the metadata of this node is changed.
    #   \param container The container whose metadata changed.
    #   \param kwargs Key-word arguments provided when changing the metadata.
    #   These are ignored. As far as I know they are never provided to this
    #   call.
    def _onMetadataChanged(self, container: ContainerInterface, **kwargs: Any) -> None:
        if container.getId() != self.container_id:
            return

        new_metadata = container.getMetaData()
        old_base_file = self.base_file
        if new_metadata["base_file"] != old_base_file:
            self.base_file = new_metadata["base_file"]
            if old_base_file in self.variant.materials:  # Move in parent node.
                del self.variant.materials[old_base_file]
            self.variant.materials[self.base_file] = self

        old_material_type = self.material_type
        self.material_type = new_metadata["material"]
        old_guid = self.guid
        self.guid = new_metadata["GUID"]
        if self.base_file != old_base_file or self.material_type != old_material_type or self.guid != old_guid:  # List of quality profiles could've changed.
            self.qualities = {}
            self._loadAll()  # Re-load the quality profiles for this node.