# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING

from UM.Settings.ContainerRegistry import ContainerRegistry  # To find all the variants for this machine.
from UM.Settings.Interfaces import ContainerInterface
from cura.Machines.ContainerNode import ContainerNode
from cura.Machines.VariantNode import VariantNode

if TYPE_CHECKING:
    from typing import Dict

##  This class represents a machine in the container tree.
#
#   The subnodes of these nodes are variants.
class MachineNode(ContainerNode):
    def __init__(self, container_id: str) -> None:
        super().__init__(container_id, None)
        self.variants = {}  # type: Dict[str, VariantNode] # mapping variant names to their nodes.
        container_registry = ContainerRegistry.getInstance()
        container_registry.containerAdded.connect(self._variantAdded)

        # Find all the variants for this definition ID.
        variants = container_registry.findInstanceContainersMetadata(type = "variant", definition = self.container_id, hardware_type = "nozzle")
        for variant in variants:
            variant_name = variant["name"]
            if variant_name not in self.variants:
                self.variants[variant_name] = VariantNode(variant["id"], parent = self)

    ##  When a variant gets added to the set of profiles, we need to update our
    #   tree here.
    def _variantAdded(self, container: ContainerInterface):
        if container.getMetaDataEntry("type") != "variant":
            return  # Not interested.
        name = container.getMetaDataEntry("name")
        if name in self.variants:
            return  # Already have this one.

        self.variants[name] = VariantNode(container.getId(), parent = self)