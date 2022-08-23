# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt6.QtCore import Qt, QTimer
from typing import Optional, Dict

from UM.Qt.ListModel import ListModel
from UM.Settings.ContainerStack import ContainerStack
from UM.i18n import i18nCatalog
from UM.Util import parseBool

from cura.PrinterOutput.PrinterOutputDevice import ConnectionType
from cura.Settings.AbstractMachine import AbstractMachine
from cura.Settings.CuraContainerRegistry import CuraContainerRegistry
from cura.Settings.GlobalStack import GlobalStack


class MachineListModel(ListModel):
    NameRole = Qt.ItemDataRole.UserRole + 1
    IdRole = Qt.ItemDataRole.UserRole + 2
    HasRemoteConnectionRole = Qt.ItemDataRole.UserRole + 3
    ConnectionTypeRole = Qt.ItemDataRole.UserRole + 4
    MetaDataRole = Qt.ItemDataRole.UserRole + 5
    DiscoverySourceRole = Qt.ItemDataRole.UserRole + 6
    RemovalWarningRole = Qt.ItemDataRole.UserRole + 7
    IsOnlineRole = Qt.ItemDataRole.UserRole + 8
    MachineTypeRole = Qt.ItemDataRole.UserRole + 9
    MachineCountRole = Qt.ItemDataRole.UserRole + 10

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._catalog = i18nCatalog("cura")

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.IdRole, "id")
        self.addRoleName(self.HasRemoteConnectionRole, "hasRemoteConnection")
        self.addRoleName(self.MetaDataRole, "metadata")
        self.addRoleName(self.DiscoverySourceRole, "discoverySource")
        self.addRoleName(self.IsOnlineRole, "isOnline")
        self.addRoleName(self.MachineTypeRole, "machineType")
        self.addRoleName(self.MachineCountRole, "machineCount")

        self._change_timer = QTimer()
        self._change_timer.setInterval(200)
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self._update)

        # Listen to changes
        CuraContainerRegistry.getInstance().containerAdded.connect(self._onContainerChanged)
        CuraContainerRegistry.getInstance().containerMetaDataChanged.connect(self._onContainerChanged)
        CuraContainerRegistry.getInstance().containerRemoved.connect(self._onContainerChanged)
        self._updateDelayed()

    def _onContainerChanged(self, container) -> None:
        """Handler for container added/removed events from registry"""

        # We only need to update when the added / removed container GlobalStack
        if isinstance(container, GlobalStack):
            self._updateDelayed()

    def _updateDelayed(self) -> None:
        self._change_timer.start()

    def _update(self) -> None:
        items = []

        abstract_machine_stacks = CuraContainerRegistry.getInstance().findContainerStacks(type="abstract_machine")

        abstract_machine_stacks.sort(key=lambda machine: machine.getName(), reverse=True)

        for abstract_machine in abstract_machine_stacks:
            machine_stacks = AbstractMachine.getMachines(abstract_machine)


            # Create item for abstract printer
            items.append(self.createItem(abstract_machine, len(machine_stacks)))

            # Create list of printers that are children of the abstract printer
            for stack in machine_stacks:
                item = self.createItem(stack)
                if item:
                    items.append(item)

        self.setItems(items)

    def createItem(self, container_stack: ContainerStack, machine_count: int = 0) -> Optional[Dict]:
        if parseBool(container_stack.getMetaDataEntry("hidden", False)):
            return

        has_remote_connection = False

        for connection_type in container_stack.configuredConnectionTypes:
            has_remote_connection |= connection_type in [ConnectionType.NetworkConnection.value,
                                                         ConnectionType.CloudConnection.value]

        device_name = container_stack.getMetaDataEntry("group_name", container_stack.getName())
        default_removal_warning = self._catalog.i18nc(
            "@label {0} is the name of a printer that's about to be deleted.",
            "Are you sure you wish to remove {0}? This cannot be undone!", device_name
        )

        return {"name": device_name,
                "id": container_stack.getId(),
                "hasRemoteConnection": has_remote_connection,
                "metadata": container_stack.getMetaData().copy(),
                "section": self._catalog.i18nc("@label", "Connected printers"),
                "removalWarning": container_stack.getMetaDataEntry("removal_warning", default_removal_warning),
                "isOnline": container_stack.getMetaDataEntry("is_online", False),
                "machineType": container_stack.getMetaDataEntry("type"),
                "machineCount": machine_count,
                }
