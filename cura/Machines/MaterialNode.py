# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional, Dict

from .ContainerNode import ContainerNode


#
# A MaterialNode is a node in the material lookup tree/map/table. It contains 2 (extra) fields:
#  - material_map: a one-to-one map of "material_root_id" to material_node.
#  - children_map: the key-value map for child nodes of this node. This is used in a lookup tree.
#
#
class MaterialNode(ContainerNode):
    __slots__ = ("material_map", "children_map")

    def __init__(self, metadata: Optional[dict] = None) -> None:
        super().__init__(metadata = metadata)
        self.material_map = {}  # type: Dict[str, MaterialNode] # material_root_id -> material_node
