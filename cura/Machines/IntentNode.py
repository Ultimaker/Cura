# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING

from cura.Machines.ContainerNode import ContainerNode

if TYPE_CHECKING:
    from cura.Machines.QualityNode import QualityNode

##  This class represents an intent profile in the container tree.
#
#   This class has no more subnodes.
class IntentNode(ContainerNode):
    def __init__(self, container_id: str, quality: "QualityNode") -> None:
        super().__init__(container_id)
        self.quality = quality