# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING

from cura.Machines.ContainerNode import ContainerNode
from cura.Machines.MachineNode import MachineNode
from cura.Machines.MaterialNode import MaterialNode

if TYPE_CHECKING:
    from typing import Dict

##  This class represents an extruder variant in the container tree.
#
#   The subnodes of these nodes are materials.
class VariantNode(ContainerNode):
    def __init__(self, container_id: str, parent: MachineNode) -> None:
        super().__init__(container_id, parent)
        self.variants = {}  # type: Dict[str, MaterialNode] # mapping variant IDs to their nodes.