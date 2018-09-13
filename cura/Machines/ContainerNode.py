# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, Any, Dict, Union, TYPE_CHECKING

from collections import OrderedDict

from UM.ConfigurationErrorMessage import ConfigurationErrorMessage
from UM.Logger import Logger
from UM.Settings.InstanceContainer import InstanceContainer

if TYPE_CHECKING:
    from cura.Machines.QualityGroup import QualityGroup


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
    __slots__ = ("_metadata", "container", "children_map")

    def __init__(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        self._metadata = metadata
        self.container = None
        self.children_map = OrderedDict()  # type: ignore  # This is because it's children are supposed to override it.

    ##  Get an entry value from the metadata
    def getMetaDataEntry(self, entry: str, default: Any = None) -> Any:
        if self._metadata is None:
            return default
        return self._metadata.get(entry, default)

    def getMetadata(self) -> Dict[str, Any]:
        if self._metadata is None:
            return {}
        return self._metadata

    def getChildNode(self, child_key: str) -> Optional["ContainerNode"]:
        return self.children_map.get(child_key)

    def getContainer(self) -> Optional["InstanceContainer"]:
        if self._metadata is None:
            Logger.log("e", "Cannot get container for a ContainerNode without metadata.")
            return None

        if self.container is None:
            container_id = self._metadata["id"]
            from UM.Settings.ContainerRegistry import ContainerRegistry
            container_list = ContainerRegistry.getInstance().findInstanceContainers(id = container_id)
            if not container_list:
                Logger.log("e", "Failed to lazy-load container [{container_id}]. Cannot find it.".format(container_id = container_id))
                error_message = ConfigurationErrorMessage.getInstance()
                error_message.addFaultyContainers(container_id)
                return None
            self.container = container_list[0]

        return self.container

    def __str__(self) -> str:
        return "%s[%s]" % (self.__class__.__name__, self.getMetaDataEntry("id"))
