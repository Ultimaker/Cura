# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING

from cura.Machines.ContainerNode import ContainerNode
from cura.Machines.ContainerTree import ContainerTree
from cura.Machines.VariantNode import VariantNode

if TYPE_CHECKING:
    from typing import Dict

##  This class represents a machine in the container tree.
#
#   The subnodes of these nodes are variants.
class MachineNode(ContainerNode):
    def __init__(self, container_id: str) -> None:
        super().__init__(container_id, None)
        self.variants = {}  # type: Dict[str, VariantNode] # mapping variant IDs to their nodes.