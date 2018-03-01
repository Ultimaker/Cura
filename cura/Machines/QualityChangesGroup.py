# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Application import Application

from .QualityGroup import QualityGroup


class QualityChangesGroup(QualityGroup):

    def __init__(self, name: str, quality_type: str, parent = None):
        super().__init__(name, quality_type, parent)
        self._container_registry = Application.getInstance().getContainerRegistry()

    def addNode(self, node: "QualityNode"):
        # TODO: in 3.2 and earlier, a quality_changes container may have a field called "extruder" which contains the
        # extruder definition ID it belongs to. But, in fact, we only need to know the following things:
        #  1. which machine a custom profile is suitable for,
        #  2. if this profile is for the GlobalStack,
        #  3. if this profile is for an ExtruderStack and which one (the position).
        #
        # So, it is preferred to have a field like this:
        #     extruder_position = 1
        # instead of this:
        #     extruder = custom_extruder_1
        #
        # An upgrade needs to be done if we want to do it this way. Before that, we use the extruder's definition
        # to figure out its position.
        #
        extruder_definition_id = node.metadata.get("extruder")
        if extruder_definition_id:
            metadata_list = self._container_registry.findDefinitionContainersMetadata(id = extruder_definition_id)
            if not metadata_list:
                raise RuntimeError("%s cannot get metadata for extruder definition [%s]" %
                                   (self, extruder_definition_id))
            extruder_definition_metadata = metadata_list[0]
            extruder_position = str(extruder_definition_metadata["position"])

            if extruder_position in self.nodes_for_extruders:
                raise RuntimeError("%s tries to overwrite the existing nodes_for_extruders position [%s] %s with %s" %
                                   (self, extruder_position, self.node_for_global, node))

            self.nodes_for_extruders[extruder_position] = node

        else:
            # This is a quality_changes for the GlobalStack
            if self.node_for_global is not None:
                raise RuntimeError("%s tries to overwrite the existing node_for_global %s with %s" %
                                   (self, self.node_for_global, node))
            self.node_for_global = node

    def __str__(self) -> str:
        return "%s[<%s>, available = %s]" % (self.__class__.__name__, self.name, self.is_available)
