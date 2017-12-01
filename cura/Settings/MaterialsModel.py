# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

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
            self._update()

    def _onContainerChanged(self, container):
        if container.getMetaDataEntry("type", "") == "material":
            super()._onContainerChanged(container)
