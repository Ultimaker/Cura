# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import List, Optional

from PyQt5.Qt import QObject, pyqtSlot

from cura.Machines.ContainerNode import ContainerNode


class ContainerGroup(QObject):

    def __init__(self, name: str, parent = None):
        super().__init__(parent)
        self.name = name
        self.node_for_global = None  # type: Optional[ContainerNode]
        self.nodes_for_extruders = dict()

    @pyqtSlot(result = str)
    def getName(self) -> str:
        return self.name

    def getAllKeys(self) -> set:
        result = set()
        for node in [self.node_for_global] + list(self.nodes_for_extruders.values()):
            if node is None:
                continue
            for key in node.getContainer().getAllKeys():
                result.add(key)
        return result

    def getAllNodes(self) -> List[ContainerNode]:
        result = []
        if self.node_for_global is not None:
            result.append(self.node_for_global)
        for extruder_node in self.nodes_for_extruders.values():
            result.append(extruder_node)
        return result
