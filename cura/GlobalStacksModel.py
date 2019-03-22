# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.


from UM.Qt.ListModel import ListModel

from PyQt5.QtCore import pyqtProperty, Qt, QTimer

from cura.PrinterOutputDevice import ConnectionType
from cura.Settings.CuraContainerRegistry import CuraContainerRegistry

from cura.Settings.GlobalStack import GlobalStack


class GlobalStacksModel(ListModel):
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
        self.addRoleName(self.MetaDataRole, "metadata")
        self._container_stacks = []

        self._change_timer = QTimer()
        self._change_timer.setInterval(200)
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self._update)

        # Listen to changes
        CuraContainerRegistry.getInstance().containerAdded.connect(self._onContainerChanged)
        CuraContainerRegistry.getInstance().containerMetaDataChanged.connect(self._onContainerChanged)
        CuraContainerRegistry.getInstance().containerRemoved.connect(self._onContainerChanged)
        self._filter_dict = {}
        self._updateDelayed()

    ##  Handler for container added/removed events from registry
    def _onContainerChanged(self, container):
        # We only need to update when the added / removed container GlobalStack
        if isinstance(container, GlobalStack):
            self._updateDelayed()

    def _updateDelayed(self):
        self._change_timer.start()

    def _update(self) -> None:
        items = []

        container_stacks = CuraContainerRegistry.getInstance().findContainerStacks(type = "machine")

        for container_stack in container_stacks:
            has_remote_connection = False

            for connection_type in container_stack.configuredConnectionTypes:
                has_remote_connection |= connection_type in [ConnectionType.NetworkConnection.value, ConnectionType.CloudConnection.value]

            if container_stack.getMetaDataEntry("hidden", False) in ["True", True]:
                continue

            items.append({"name": container_stack.getMetaDataEntry("group_name", container_stack.getName()),
                          "id": container_stack.getId(),
                          "hasRemoteConnection": has_remote_connection,
                          "metadata": container_stack.getMetaData().copy()})
        items.sort(key=lambda i: not i["hasRemoteConnection"])
        self.setItems(items)
