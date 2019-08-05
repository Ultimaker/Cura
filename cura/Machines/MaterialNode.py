# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING

from cura.Machines.ContainerNode import ContainerNode
from cura.Machines.QualityNode import QualityNode
from cura.Machines.VariantNode import VariantNode

if TYPE_CHECKING:
    from typing import Dict

##  Represents a material in the container tree.
#
#   Its subcontainers are quality profiles.
class MaterialNode(ContainerNode):
    def __init__(self, container_id, parent: VariantNode) -> None:
        super().__init__(container_id, parent)
        self.qualities = {}  # type: Dict[str, QualityNode] # Mapping container IDs to quality profiles.