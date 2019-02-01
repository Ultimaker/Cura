# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Qt.ListModel import ListModel

from PyQt5.QtCore import Qt

from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.ContainerStack import ContainerStack

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


#
# This the QML model for the quality management page.
#
class MachineManagementModel(ListModel):
    NameRole = Qt.UserRole + 1
    IdRole = Qt.UserRole + 2
    MetaDataRole = Qt.UserRole + 3
    GroupRole = Qt.UserRole + 4

    def __init__(self, parent = None):
        super().__init__(parent)
        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.IdRole, "id")
        self.addRoleName(self.MetaDataRole, "metadata")
        self.addRoleName(self.GroupRole, "group")
        self._local_container_stacks = []
        self._network_container_stacks = []

        # Listen to changes
        ContainerRegistry.getInstance().containerAdded.connect(self._onContainerChanged)
        ContainerRegistry.getInstance().containerMetaDataChanged.connect(self._onContainerChanged)
        ContainerRegistry.getInstance().containerRemoved.connect(self._onContainerChanged)
        self._filter_dict = {}
        self._update()

    ##  Handler for container added/removed events from registry
    def _onContainerChanged(self, container):
        # We only need to update when the added / removed container is a stack.
        if isinstance(container, ContainerStack) and container.getMetaDataEntry("type") == "machine":
            self._update()

    ##  Private convenience function to reset & repopulate the model.
    def _update(self):
        items = []

        # Get first the network enabled printers
        network_filter_printers = {"type": "machine",
                                   "um_network_key": "*",
                                   "hidden": "False"}
        self._network_container_stacks = ContainerRegistry.getInstance().findContainerStacks(**network_filter_printers)
        self._network_container_stacks.sort(key = lambda i: i.getMetaDataEntry("group_name", ""))

        for container in self._network_container_stacks:
            metadata = container.getMetaData().copy()
            if container.getBottom():
                metadata["definition_name"] = container.getBottom().getName()

            items.append({"name": metadata.get("group_name", ""),
                          "id": container.getId(),
                          "metadata": metadata,
                          "group": catalog.i18nc("@info:title", "Network enabled printers")})

        # Get now the local printers
        local_filter_printers = {"type": "machine", "um_network_key": None}
        self._local_container_stacks = ContainerRegistry.getInstance().findContainerStacks(**local_filter_printers)
        self._local_container_stacks.sort(key = lambda i: i.getName())

        for container in self._local_container_stacks:
            metadata = container.getMetaData().copy()
            if container.getBottom():
                metadata["definition_name"] = container.getBottom().getName()

            items.append({"name": container.getName(),
                          "id": container.getId(),
                          "metadata": metadata,
                          "group": catalog.i18nc("@info:title", "Local printers")})

        self.setItems(items)
