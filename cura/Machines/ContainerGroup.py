from typing import Optional

from PyQt5.Qt import QObject

from cura.Machines.ContainerNode import ContainerNode


class ContainerGroup(QObject):

    def __init__(self, parent = None):
        super().__init__(parent)
        self.node_for_global = None  # type: Optional[ContainerNode]
        self.nodes_for_extruders = dict()
