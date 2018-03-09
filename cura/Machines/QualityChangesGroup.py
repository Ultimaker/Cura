# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Application import Application

from .QualityGroup import QualityGroup


class QualityChangesGroup(QualityGroup):
    def __init__(self, name: str, quality_type: str, parent = None):
        super().__init__(name, quality_type, parent)
        self._container_registry = Application.getInstance().getContainerRegistry()

    def addNode(self, node: "QualityNode"):
        extruder_position = node.metadata.get("position")
        if extruder_position is None: #Then we're a global quality changes profile.
            if self.node_for_global is not None:
                raise RuntimeError("{group} tries to overwrite the existing node_for_global {original_global} with {new_global}".format(group = self, original_global = self.node_for_global, new_global = node))
            self.node_for_global = node
        else: #This is an extruder's quality changes profile.
            if extruder_position in self.nodes_for_extruders:
                raise RuntimeError("%s tries to overwrite the existing nodes_for_extruders position [%s] %s with %s" %
                                   (self, extruder_position, self.node_for_global, node))
            self.nodes_for_extruders[extruder_position] = node

    def __str__(self) -> str:
        return "%s[<%s>, available = %s]" % (self.__class__.__name__, self.name, self.is_available)
