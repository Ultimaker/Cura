from typing import Optional

from collections import OrderedDict

from UM.Logger import Logger


##  A metadata / container combination. Use getContainer to get the container corresponding to the metadata
class ContainerNode:
    def __init__(self, metadata = None):
        self.metadata = metadata
        self.container = None
        self.children_map = OrderedDict()

    def getChildNode(self, child_key: str) -> Optional["QualityNode"]:
        return self.children_map.get(child_key)

    def getContainer(self) -> "InstanceContainer":
        if self.metadata is None:
            raise RuntimeError("Cannot get container for a QualityNode without metadata")

        if self.container is None:
            container_id = self.metadata["id"]
            Logger.log("d", "Lazy-loading container [%s]", container_id)
            from UM.Settings.ContainerRegistry import ContainerRegistry
            container_list = ContainerRegistry.getInstance().findInstanceContainers(id = container_id)
            if not container_list:
                raise RuntimeError("Failed to lazy-load container [%s], cannot find it" % container_id)
            self.container = container_list[0]

        return self.container

    def __str__(self):
        return "ContainerNode[%s]" % self.metadata.get("id")
