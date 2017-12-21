# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, List
from UM.Settings.ContainerRegistry import ContainerRegistry #To listen for changes to the materials.
from UM.Settings.Models.InstanceContainersModel import InstanceContainersModel #We're extending this class.

##  A model that shows a list of currently valid materials.
class MaterialsModel(InstanceContainersModel):
    def __init__(self, parent = None):
        super().__init__(parent)

        ContainerRegistry.getInstance().containerMetaDataChanged.connect(self._onContainerMetaDataChanged)

    ##  Called when the metadata of the container was changed.
    #
    #   This makes sure that we only update when it was a material that changed.
    #
    #   \param container The container whose metadata was changed.
    def _onContainerMetaDataChanged(self, container):
        if container.getMetaDataEntry("type") == "material": #Only need to update if a material was changed.
            self._container_change_timer.start()

    def _onContainerChanged(self, container):
        if container.getMetaDataEntry("type", "") == "material":
            super()._onContainerChanged(container)

    ##  Group brand together
    def _sortKey(self, item) -> List[Any]:
        result = []
        result.append(item["metadata"]["brand"])
        result.append(item["metadata"]["material"])
        result.append(item["metadata"]["name"])
        result.append(item["metadata"]["color_name"])
        result.append(item["metadata"]["id"])
        result.extend(super()._sortKey(item))
        return result
