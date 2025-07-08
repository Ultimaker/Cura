# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, Optional

from UM.ConfigurationErrorMessage import ConfigurationErrorMessage
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Logger import Logger
from UM.Settings.InstanceContainer import InstanceContainer


class ContainerNode:
    """A node in the container tree. It represents one container.

    The container it represents is referenced by its container_id. During normal use of the tree, this container is
    not constructed. Only when parts of the tree need to get loaded in the container stack should it get constructed.
    """

    def __init__(self, container_id: str) -> None:
        """Creates a new node for the container tree.

        :param container_id: The ID of the container that this node should represent.
        """

        self.container_id = container_id
        self._container = None  # type: Optional[InstanceContainer]
        self.children_map = {}  # type: Dict[str, ContainerNode]  # Mapping from container ID to container node.

    def getMetadata(self) -> Dict[str, Any]:
        """Gets the metadata of the container that this node represents.

        Getting the metadata from the container directly is about 10x as fast.

        :return: The metadata of the container in this node.
        """

        return ContainerRegistry.getInstance().findContainersMetadata(id=self.container_id)[0]

    def getMetaDataEntry(self, entry: str, default: Any = None) -> Any:
        """Get an entry from the metadata of the container that this node contains.

        This is just a convenience function.

        :param entry: The metadata entry key to return.
        :param default: If the metadata is not present or the container is not found, the value of this default is
        returned.

        :return: The value of the metadata entry, or the default if it was not present.
        """

        container_metadata = ContainerRegistry.getInstance().findContainersMetadata(id=self.container_id)
        if len(container_metadata) == 0:
            return default
        return container_metadata[0].get(entry, default)

    @property
    def container(self) -> Optional[InstanceContainer]:
        """The container that this node's container ID refers to.

        This can be used to finally instantiate the container in order to put it in the container stack.

        :return: A container.
        """

        if not self._container:
            container_list = ContainerRegistry.getInstance().findInstanceContainers(id=self.container_id)
            if len(container_list) == 0:
                Logger.log("e", "Failed to lazy-load container [{container_id}]. Cannot find it.".format(container_id=self.container_id))
                error_message = ConfigurationErrorMessage.getInstance()
                error_message.addFaultyContainers(self.container_id)
                return None
            self._container = container_list[0]
        return self._container

    def __str__(self) -> str:
        return "%s[%s]" % (self.__class__.__name__, self.container_id)
