# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Dict, Optional, List, Set

from PyQt5.QtCore import QObject, pyqtSlot

from UM.Logger import Logger
from UM.Util import parseBool

from cura.Machines.ContainerNode import ContainerNode


##  A QualityGroup represents a group of quality containers that must be applied
#   to each ContainerStack when it's used.
#
#   A concrete example: When there are two extruders and the user selects the
#   quality type "normal", this quality type must be applied to all stacks in a
#   machine, although each stack can have different containers. So one global
#   profile gets put on the global stack and one extruder profile gets put on
#   each extruder stack. This quality group then contains the following
#   profiles (for instance):
#                      GlobalStack       ExtruderStack 1     ExtruderStack 2
#   quality container: um3_global_normal um3_aa04_pla_normal um3_aa04_abs_normal
#
#   The purpose of these quality groups is to group the containers that can be
#   applied to a configuration, so that when a quality level is selected, the
#   container can directly be applied to each stack instead of looking them up
#   again.
class QualityGroup:
    ##  Constructs a new group.
    #   \param name The user-visible name for the group.
    #   \param quality_type The quality level that each profile in this group
    #   has.
    def __init__(self, name: str, quality_type: str) -> None:
        self.name = name
        self.node_for_global = None  # type: Optional[ContainerNode]
        self.nodes_for_extruders = {}  # type: Dict[int, ContainerNode]
        self.quality_type = quality_type
        self.is_available = False
        self.is_experimental = False

    def getName(self) -> str:
        return self.name

    def getAllKeys(self) -> Set[str]:
        result = set()  # type: Set[str]
        for node in [self.node_for_global] + list(self.nodes_for_extruders.values()):
            if node is None:
                continue
            container = node.container
            if container:
                result.update(container.getAllKeys())
        return result

    def getAllNodes(self) -> List[ContainerNode]:
        result = []
        if self.node_for_global is not None:
            result.append(self.node_for_global)
        for extruder_node in self.nodes_for_extruders.values():
            result.append(extruder_node)
        return result

    def setGlobalNode(self, node: "ContainerNode") -> None:
        self.node_for_global = node

        # Update is_experimental flag
        if not node.container:
            Logger.log("w", "Node {0} doesn't have a container.".format(node.container_id))
            return
        is_experimental = parseBool(node.container.getMetaDataEntry("is_experimental", False))
        self.is_experimental |= is_experimental

    def setExtruderNode(self, position: int, node: "ContainerNode") -> None:
        self.nodes_for_extruders[position] = node

        # Update is_experimental flag
        if not node.container:
            Logger.log("w", "Node {0} doesn't have a container.".format(node.container_id))
            return
        is_experimental = parseBool(node.container.getMetaDataEntry("is_experimental", False))
        self.is_experimental |= is_experimental
