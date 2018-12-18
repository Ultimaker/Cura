# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Qt.ListModel import ListModel

from PyQt5.QtCore import pyqtProperty, Qt, pyqtSignal

from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.ContainerStack import ContainerStack

from cura.PrinterOutputDevice import ConnectionType

from cura.Settings.GlobalStack import GlobalStack

class PrintersModel(ListModel):
    NameRole = Qt.UserRole + 1
    IdRole = Qt.UserRole + 2
    HasRemoteConnectionRole = Qt.UserRole + 3
    ConnectionTypeRole = Qt.UserRole + 4
    MetaDataRole = Qt.UserRole + 5

    def __init__(self, parent = None):
        super().__init__(parent)
        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.IdRole, "id")
        self.addRoleName(self.HasRemoteConnectionRole, "hasRemoteConnection")
        self.addRoleName(self.ConnectionTypeRole, "connectionType")
        self.addRoleName(self.MetaDataRole, "metadata")
        self._container_stacks = []

        # Listen to changes
        ContainerRegistry.getInstance().containerAdded.connect(self._onContainerChanged)
        ContainerRegistry.getInstance().containerMetaDataChanged.connect(self._onContainerChanged)
        ContainerRegistry.getInstance().containerRemoved.connect(self._onContainerChanged)
        self._filter_dict = {}
        self._update()

    ##  Handler for container added/removed events from registry
    def _onContainerChanged(self, container):
        # We only need to update when the added / removed container GlobalStack
        if isinstance(container, GlobalStack):
            self._update()

    ##  Handler for container name change events.
    def _onContainerNameChanged(self):
        self._update()

    def _update(self) -> None:
        items = []
        for container in self._container_stacks:
            container.nameChanged.disconnect(self._onContainerNameChanged)

        container_stacks = ContainerRegistry.getInstance().findContainerStacks(type = "machine")

        for container_stack in container_stacks:
            connection_type = container_stack.getMetaDataEntry("connection_type")
            has_remote_connection = connection_type in [ConnectionType.NetworkConnection.value, ConnectionType.CloudConnection.value]

            if container_stack.getMetaDataEntry("hidden", False) in ["True", True]:
                continue

            # TODO: Remove reference to connect group name.
            items.append({"name": container_stack.getMetaDataEntry("connect_group_name", container_stack.getName()),
                          "id": container_stack.getId(),
                          "hasRemoteConnection": has_remote_connection,
                          "connectionType": connection_type,
                          "metadata": container_stack.getMetaData().copy()})
        items.sort(key=lambda i: not i["hasRemoteConnection"])
        self.setItems(items)