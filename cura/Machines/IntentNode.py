# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING

from cura.Machines.ContainerNode import ContainerNode
from cura.Machines.MaterialNode import MaterialNode
from cura.Machines.QualityNode import QualityNode

if TYPE_CHECKING:
    from typing import Dict

##  This class represents an intent category in the container tree.
#
#   This class has no more subnodes.
class IntentNode(ContainerNode):
    def __init__(self, container_id: str, parent: QualityNode) -> None:
        super().__init__(container_id, parent)
        self.variants = {}  # type: Dict[str, MaterialNode] # mapping variant IDs to their nodes.