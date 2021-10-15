# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt, QTimer, pyqtProperty, pyqtSignal
from typing import Optional

from UM.Qt.ListModel import ListModel
from UM.i18n import i18nCatalog
from UM.Util import parseBool

from cura.PrinterOutput.PrinterOutputDevice import ConnectionType
from cura.Settings.CuraContainerRegistry import CuraContainerRegistry
from cura.Settings.GlobalStack import GlobalStack


class GlobalStacksModel(ListModel):
    NameRole = Qt.UserRole + 1
    IdRole = Qt.UserRole + 2
    HasRemoteConnectionRole = Qt.UserRole + 3
    ConnectionTypeRole = Qt.UserRole + 4
    MetaDataRole = Qt.UserRole + 5
    DiscoverySourceRole = Qt.UserRole + 6  # For separating local and remote printers in the machine management page
    RemovalWarningRole = Qt.UserRole + 7
    IsOnlineRole = Qt.UserRole + 8

    def __init__(self, parent = None) -> None:
        super().__init__(parent)

        self._catalog = i18nCatalog("cura")

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.IdRole, "id")
        self.addRoleName(self.HasRemoteConnectionRole, "hasRemoteConnection")
        self.addRoleName(self.MetaDataRole, "metadata")
        self.addRoleName(self.DiscoverySourceRole, "discoverySource")
        self.addRoleName(self.IsOnlineRole, "isOnline")

        self._change_timer = QTimer()
        self._change_timer.setInterval(200)
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self._update)

        self._filter_connection_type = None  # type: Optional[ConnectionType]
        self._filter_online_only = False

        # Listen to changes
        CuraContainerRegistry.getInstance().containerAdded.connect(self._onContainerChanged)
        CuraContainerRegistry.getInstance().containerMetaDataChanged.connect(self._onContainerChanged)
        CuraContainerRegistry.getInstance().containerRemoved.connect(self._onContainerChanged)
        self._updateDelayed()

    filterConnectionTypeChanged = pyqtSignal()
    def setFilterConnectionType(self, new_filter: Optional[ConnectionType]) -> None:
        self._filter_connection_type = new_filter

    @pyqtProperty(int, fset = setFilterConnectionType, notify = filterConnectionTypeChanged)
    def filterConnectionType(self) -> int:
        """
        The connection type to filter the list of printers by.

        Only printers that match this connection type will be listed in the
        model.
        """
        if self._filter_connection_type is None:
            return -1
        return self._filter_connection_type.value

    filterOnlineOnlyChanged = pyqtSignal()
    def setFilterOnlineOnly(self, new_filter: bool) -> None:
        self._filter_online_only = new_filter

    @pyqtProperty(bool, fset = setFilterOnlineOnly, notify = filterOnlineOnlyChanged)
    def filterOnlineOnly(self) -> bool:
        """
        Whether to filter the global stacks to show only printers that are online.
        """
        return self._filter_online_only

    def _onContainerChanged(self, container) -> None:
        """Handler for container added/removed events from registry"""

        # We only need to update when the added / removed container GlobalStack
        if isinstance(container, GlobalStack):
            self._updateDelayed()

    def _updateDelayed(self) -> None:
        self._change_timer.start()

    def _update(self) -> None:
        items = []

        container_stacks = CuraContainerRegistry.getInstance().findContainerStacks(type = "machine")
        for container_stack in container_stacks:
            if self._filter_connection_type is not None:  # We want to filter on connection types.
                if not any((connection_type == self._filter_connection_type for connection_type in container_stack.configuredConnectionTypes)):
                    continue  # No connection type on this printer matches the filter.

            has_remote_connection = False

            for connection_type in container_stack.configuredConnectionTypes:
                has_remote_connection |= connection_type in [ConnectionType.NetworkConnection.value,
                                                             ConnectionType.CloudConnection.value]

            if parseBool(container_stack.getMetaDataEntry("hidden", False)):
                continue

            is_online = container_stack.getMetaDataEntry("is_online", False)
            if self._filter_online_only and not is_online:
                continue

            device_name = container_stack.getMetaDataEntry("group_name", container_stack.getName())
            section_name = "Connected printers" if has_remote_connection else "Preset printers"
            section_name = self._catalog.i18nc("@info:title", section_name)

            default_removal_warning = self._catalog.i18nc(
                "@label {0} is the name of a printer that's about to be deleted.",
                "Are you sure you wish to remove {0}? This cannot be undone!", device_name
            )
            removal_warning = container_stack.getMetaDataEntry("removal_warning", default_removal_warning)

            items.append({"name": device_name,
                          "id": container_stack.getId(),
                          "hasRemoteConnection": has_remote_connection,
                          "metadata": container_stack.getMetaData().copy(),
                          "discoverySource": section_name,
                          "removalWarning": removal_warning,
                          "isOnline": is_online})
        items.sort(key=lambda i: (not i["hasRemoteConnection"], i["name"]))
        self.setItems(items)
