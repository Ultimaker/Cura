# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, Dict, cast, Any, Tuple

from .ContainerNode import ContainerNode
from .QualityChangesGroup import QualityChangesGroup


#
# QualityNode is used for BOTH quality and quality_changes containers.
#
class QualityNode(ContainerNode):

    def __init__(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(metadata = metadata)
        self.quality_type_map = {}  # type: Dict[Tuple[str, str], QualityNode] # quality_type -> QualityNode for InstanceContainer

    def getChildNode(self, child_key: str) -> Optional["QualityNode"]:
        return self.children_map.get(child_key)

    def addQualityMetadata(self, quality_tuple: Tuple[str, str], metadata: Dict[str, Any]):
        if quality_tuple not in self.quality_type_map:
            self.quality_type_map[quality_tuple] = QualityNode(metadata)

    def getQualityNode(self, quality_tuple: Tuple[str, str]) -> Optional["QualityNode"]:
        return self.quality_type_map.get(quality_tuple)

    def addQualityChangesMetadata(self, quality_tuple: Tuple[str, str], metadata: Dict[str, Any]):
        if quality_tuple not in self.quality_type_map:
            self.quality_type_map[quality_tuple] = QualityNode()
        quality_type_node = self.quality_type_map[quality_tuple]

        name = metadata["name"]
        if name not in quality_type_node.children_map:
            quality_type_node.children_map[name] = QualityChangesGroup(name, quality_tuple)
        quality_changes_group = quality_type_node.children_map[name]
        cast(QualityChangesGroup, quality_changes_group).addNode(QualityNode(metadata))
