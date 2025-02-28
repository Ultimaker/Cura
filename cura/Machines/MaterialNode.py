# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Optional, TYPE_CHECKING

from UM.Logger import Logger
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.Interfaces import ContainerInterface
from UM.Signal import Signal
from cura.Machines.ContainerNode import ContainerNode
from cura.Machines.QualityNode import QualityNode
import UM.FlameProfiler
if TYPE_CHECKING:
    from typing import Dict
    from cura.Machines.VariantNode import VariantNode


class MaterialNode(ContainerNode):
    """Represents a material in the container tree.

    Its subcontainers are quality profiles.
    """

    def __init__(self, container_id: str, variant: "VariantNode", *,  container: ContainerInterface = None) -> None:
        super().__init__(container_id)
        self.variant = variant
        self.qualities = {}  # type: Dict[str, QualityNode] # Mapping container IDs to quality profiles.
        self.materialChanged = Signal()  # Triggered when the material is removed or its metadata is updated.

        container_registry = ContainerRegistry.getInstance()

        if container is not None:
            self.base_file = container.getMetaDataEntry("base_file")
            self.material_type = container.getMetaDataEntry("material")
            self.brand = container.getMetaDataEntry("brand")
            self.guid = container.getMetaDataEntry("GUID")
        else:
            my_metadata = container_registry.findContainersMetadata(id = container_id)[0]
            self.base_file = my_metadata["base_file"]
            self.material_type = my_metadata["material"]
            self.brand = my_metadata["brand"]
            self.guid = my_metadata["GUID"]

        self._loadAll()
        container_registry.containerRemoved.connect(self._onRemoved)
        container_registry.containerMetaDataChanged.connect(self._onMetadataChanged)

    def preferredQuality(self) -> QualityNode:
        """Finds the preferred quality for this printer with this material and this variant loaded.

        If the preferred quality is not available, an arbitrary quality is returned. If there is a configuration
        mistake (like a typo in the preferred quality) this returns a random available quality. If there are no
        available qualities, this will return the empty quality node.

        :return: The node for the preferred quality, or any arbitrary quality if there is no match.
        """

        for quality_id, quality_node in self.qualities.items():
            if self.variant.machine.preferred_quality_type == quality_node.quality_type:
                return quality_node
        fallback = next(iter(self.qualities.values()))  # Should only happen with empty quality node.
        Logger.log("w", "Could not find preferred quality type {preferred_quality_type} for material {material_id} and variant {variant_id}, falling back to {fallback}.".format(
            preferred_quality_type=self.variant.machine.preferred_quality_type,
            material_id=self.container_id,
            variant_id=self.variant.container_id,
            fallback=fallback.container_id
        ))
        return fallback

    @UM.FlameProfiler.profile
    def _loadAll(self) -> None:
        container_registry = ContainerRegistry.getInstance()
        # Find all quality profiles that fit on this material.
        if not self.variant.machine.has_machine_quality:  # Need to find the global qualities.
            qualities = container_registry.findInstanceContainersMetadata(type="quality",
                                                                          definition="fdmprinter")
        elif not self.variant.machine.has_materials:
            qualities = container_registry.findInstanceContainersMetadata(type="quality",
                                                                          definition=self.variant.machine.quality_definition)
        else:
            if self.variant.machine.has_variants:
                # Need to find the qualities that specify a material profile with the same material type.
                qualities = container_registry.findInstanceContainersMetadata(type="quality",
                                                                              definition=self.variant.machine.quality_definition,
                                                                              variant=self.variant.variant_name,
                                                                              material=self.base_file)  # First try by exact material ID.
                # CURA-7070
                # The quality profiles only reference a material with the material_root_id. They will never state something
                # such as "generic_pla_ultimaker_s5_AA_0.4". So we search with the "base_file" which is the material_root_id.
            else:
                qualities = container_registry.findInstanceContainersMetadata(type="quality", definition=self.variant.machine.quality_definition, material=self.base_file)

            if not qualities:
                my_material_type = self.material_type
                if self.variant.machine.has_variants:
                    qualities_any_material = container_registry.findInstanceContainersMetadata(type="quality",
                                                                                               definition=self.variant.machine.quality_definition,
                                                                                               variant=self.variant.variant_name)
                else:
                    qualities_any_material = container_registry.findInstanceContainersMetadata(type="quality", definition=self.variant.machine.quality_definition)

                # First we attempt to find materials that have the same brand but not the right color
                all_material_base_files_right_brand = {material_metadata["base_file"] for material_metadata in container_registry.findInstanceContainersMetadata(type="material", material=my_material_type, brand=self.brand)}

                right_brand_no_color_qualities = [quality for quality in qualities_any_material if quality.get("material") in all_material_base_files_right_brand]

                if right_brand_no_color_qualities:
                    # We found qualties for materials with the right brand but not with the right color. Use those.
                    qualities.extend(right_brand_no_color_qualities)
                else:
                    # Fall back to generic
                    all_material_base_files = {material_metadata["base_file"] for material_metadata in
                                               container_registry.findInstanceContainersMetadata(type="material",
                                                                                                 material=my_material_type)}
                    no_brand_no_color_qualities = (quality for quality in qualities_any_material if
                                                   quality.get("material") in all_material_base_files)
                    qualities.extend(no_brand_no_color_qualities)

                if not qualities:  # No quality profiles found. Go by GUID then.
                    my_guid = self.guid
                    for material_metadata in container_registry.findInstanceContainersMetadata(type="material", guid=my_guid):
                        qualities.extend((quality for quality in qualities_any_material if quality["material"] == material_metadata["base_file"]))

                if not qualities:
                    # There are still some machines that should use global profiles in the extruder, so do that now.
                    # These are mostly older machines that haven't received updates (so single extruder machines without specific qualities
                    # but that do have materials and profiles specific to that machine)
                    qualities.extend([quality for quality in qualities_any_material if quality.get("global_quality", "False") != "False"])

        for quality in qualities:
            quality_id = quality["id"]
            if quality_id not in self.qualities:
                self.qualities[quality_id] = QualityNode(quality_id, parent=self)
        if not self.qualities:
            self.qualities["empty_quality"] = QualityNode("empty_quality", parent=self)

    def _onRemoved(self, container: ContainerInterface) -> None:
        """Triggered when any container is removed, but only handles it when the container is removed that this node
        represents.

        :param container: The container that was allegedly removed.
        """

        if container.getId() == self.container_id:
            # Remove myself from my parent.
            if self.base_file in self.variant.materials:
                del self.variant.materials[self.base_file]
                if not self.variant.materials:
                    self.variant.materials["empty_material"] = MaterialNode("empty_material", variant=self.variant)
            self.materialChanged.emit(self)

    def _onMetadataChanged(self, container: ContainerInterface, **kwargs: Any) -> None:
        """Triggered when any metadata changed in any container, but only handles it when the metadata of this node is
        changed.

        :param container: The container whose metadata changed.
        :param kwargs: Key-word arguments provided when changing the metadata. These are ignored. As far as I know they
        are never provided to this call.
        """

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
        self.materialChanged.emit(self)
