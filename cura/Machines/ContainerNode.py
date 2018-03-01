# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional

from collections import OrderedDict

from UM.Logger import Logger
from UM.Settings.InstanceContainer import InstanceContainer


##
# A metadata / container combination. Use getContainer() to get the container corresponding to the metadata.
#
# ContainerNode is a multi-purpose class. It has two main purposes:
#  1. It encapsulates an InstanceContainer. It contains that InstanceContainer's
#          - metadata (Always)
#          - container (lazy-loaded when needed)
#  2. It also serves as a node in a hierarchical InstanceContainer lookup table/tree.
#     This is used in Variant, Material, and Quality Managers.
#
class ContainerNode:
    __slots__ = ("metadata", "container", "children_map")

    def __init__(self, metadata: Optional[dict] = None):
        self.metadata = metadata
        self.container = None
        self.children_map = OrderedDict()

    def getChildNode(self, child_key: str) -> Optional["ContainerNode"]:
        return self.children_map.get(child_key)

    def getContainer(self) -> "InstanceContainer":
        if self.metadata is None:
            raise RuntimeError("Cannot get container for a ContainerNode without metadata")

        if self.container is None:
            container_id = self.metadata["id"]
            Logger.log("i", "Lazy-loading container [%s]", container_id)
            from UM.Settings.ContainerRegistry import ContainerRegistry
            container_list = ContainerRegistry.getInstance().findInstanceContainers(id = container_id)
            if not container_list:
                raise RuntimeError("Failed to lazy-load container [%s], cannot find it" % container_id)
            self.container = container_list[0]

        return self.container

    def __str__(self) -> str:
        return "%s[%s]" % (self.__class__.__name__, self.metadata.get("id"))
