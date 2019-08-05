# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, Optional

from UM.ConfigurationErrorMessage import ConfigurationErrorMessage
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Logger import Logger
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Decorators import deprecated

##  A node in the container tree. It represents one container.
#
#   The container it represents is referenced by its container_id. During normal
#   use of the tree, this container is not constructed. Only when parts of the
#   tree need to get loaded in the container stack should it get constructed.
class ContainerNode:
    ##  Creates a new node for the container tree.
    #   \param container_id The ID of the container that this node should
    #   represent.
    #   \param parent The parent container node, if any.
    def __init__(self, container_id: str, parent: Optional["ContainerNode"]) -> None:
        self.container_id = container_id
        self.parent = parent
        self._container = None  # type: Optional[InstanceContainer]
        self.children_map = {}  # type: Dict[str, ContainerNode]  # Mapping from container ID to container node.

    ##  Get an entry from the metadata of the container that this node contains.
    #   \param entry The metadata entry key to return.
    #   \param default If the metadata is not present or the container is not
    #   found, the value of this default is returned.
    #   \return The value of the metadata entry, or the default if it was not
    #   present.
    @deprecated("Get the metadata from the container with the ID of this node yourself.", "4.3")
    def getMetaDataEntry(self, entry: str, default: Any = None) -> Any:
        container_metadata = ContainerRegistry.getInstance().findContainersMetadata(id = self.container_id)
        if len(container_metadata) == 0:
            return default
        return container_metadata[0].get(entry, default)

    ##  Get the child with the specified container ID.
    #   \param child_id The container ID to get from among the children.
    #   \return The child node, or ``None`` if no child is present with the
    #   specified ID.
    @deprecated("Iterate over the children instead of requesting them one by one.", "4.3")
    def getChildNode(self, child_id: str) -> Optional["ContainerNode"]:
        return self.children_map.get(child_id)

    @deprecated("Use `.container` instead.", "4.3")
    def getContainer(self) -> Optional[InstanceContainer]:
        return self.container

    ##  The container that this node's container ID refers to.
    #
    #   This can be used to finally instantiate the container in order to put it
    #   in the container stack.
    #   \return A container.
    @property
    def container(self) -> Optional[InstanceContainer]:
        if not self._container:
            container_list = ContainerRegistry.getInstance().findInstanceContainers(id = self.container_id)
            if len(container_list) == 0:
                Logger.log("e", "Failed to lazy-load container [{container_id}]. Cannot find it.".format(container_id = self.container_id))
                error_message = ConfigurationErrorMessage.getInstance()
                error_message.addFaultyContainers(self.container_id)
                return None
            self._container = container_list[0]
        return self._container

    def __str__(self) -> str:
        return "%s[%s]" % (self.__class__.__name__, self.container_id)