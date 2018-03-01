# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional

from .ContainerNode import ContainerNode
from .QualityChangesGroup import QualityChangesGroup


#
# QualityNode is used for BOTH quality and quality_changes containers.
#
class QualityNode(ContainerNode):

    def __init__(self, metadata: Optional[dict] = None):
        super().__init__(metadata = metadata)
        self.quality_type_map = {}  # quality_type -> QualityNode for InstanceContainer

    def addQualityMetadata(self, quality_type: str, metadata: dict):
        if quality_type not in self.quality_type_map:
            self.quality_type_map[quality_type] = QualityNode(metadata)

    def getQualityNode(self, quality_type: str) -> Optional["QualityNode"]:
        return self.quality_type_map.get(quality_type)

    def addQualityChangesMetadata(self, quality_type: str, metadata: dict):
        if quality_type not in self.quality_type_map:
            self.quality_type_map[quality_type] = QualityNode()
        quality_type_node = self.quality_type_map[quality_type]

        name = metadata["name"]
        if name not in quality_type_node.children_map:
            quality_type_node.children_map[name] = QualityChangesGroup(name, quality_type)
        quality_changes_group = quality_type_node.children_map[name]
        quality_changes_group.addNode(QualityNode(metadata))
