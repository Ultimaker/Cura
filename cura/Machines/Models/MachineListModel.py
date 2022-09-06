# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

# The MachineListModel is used to display the connected printers in the interface. Both the abstract machines and all
# online cloud connected printers are represented within this ListModel. Additional information such as the number of
# connected printers for each printer type is gathered.

from PyQt6.QtCore import Qt, QTimer, pyqtSlot, pyqtProperty, pyqtSignal

from UM.Qt.ListModel import ListModel
from UM.Settings.ContainerStack import ContainerStack
from UM.i18n import i18nCatalog
from UM.Util import parseBool
from cura.PrinterOutput.PrinterOutputDevice import ConnectionType

from cura.Settings.CuraContainerRegistry import CuraContainerRegistry
from cura.Settings.GlobalStack import GlobalStack


class MachineListModel(ListModel):
    NameRole = Qt.ItemDataRole.UserRole + 1
    IdRole = Qt.ItemDataRole.UserRole + 2
    HasRemoteConnectionRole = Qt.ItemDataRole.UserRole + 3
    MetaDataRole = Qt.ItemDataRole.UserRole + 4
    IsOnlineRole = Qt.ItemDataRole.UserRole + 5
    MachineCountRole = Qt.ItemDataRole.UserRole + 6
    IsAbstractMachineRole = Qt.ItemDataRole.UserRole + 7
    ComponentTypeRole = Qt.ItemDataRole.UserRole + 8

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._show_cloud_printers = False

        self._catalog = i18nCatalog("cura")

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.IdRole, "id")
        self.addRoleName(self.HasRemoteConnectionRole, "hasRemoteConnection")
        self.addRoleName(self.MetaDataRole, "metadata")
        self.addRoleName(self.IsOnlineRole, "isOnline")
        self.addRoleName(self.MachineCountRole, "machineCount")
        self.addRoleName(self.IsAbstractMachineRole, "isAbstractMachine")
        self.addRoleName(self.ComponentTypeRole, "componentType")

        self._change_timer = QTimer()
        self._change_timer.setInterval(200)
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self._update)

        # Listen to changes
        CuraContainerRegistry.getInstance().containerAdded.connect(self._onContainerChanged)
        CuraContainerRegistry.getInstance().containerMetaDataChanged.connect(self._onContainerChanged)
        CuraContainerRegistry.getInstance().containerRemoved.connect(self._onContainerChanged)
        self._updateDelayed()

    showCloudPrintersChanged = pyqtSignal(bool)

    @pyqtProperty(bool, notify=showCloudPrintersChanged)
    def showCloudPrinters(self) -> bool:
        return self._show_cloud_printers

    @pyqtSlot(bool) 
    def setShowCloudPrinters(self, show_cloud_printers: bool) -> None:
        self._show_cloud_printers = show_cloud_printers
        self._updateDelayed()
        self.showCloudPrintersChanged.emit(show_cloud_printers)

    def _onContainerChanged(self, container) -> None:
        """Handler for container added/removed events from registry"""

        # We only need to update when the added / removed container GlobalStack
        if isinstance(container, GlobalStack):
            self._updateDelayed()

    def _updateDelayed(self) -> None:
        self._change_timer.start()

    def _update(self) -> None:
        self.clear()

        other_machine_stacks = CuraContainerRegistry.getInstance().findContainerStacks(type="machine")

        abstract_machine_stacks = CuraContainerRegistry.getInstance().findContainerStacks(is_abstract_machine = "True")
        abstract_machine_stacks.sort(key = lambda machine: machine.getName(), reverse = True)
        for abstract_machine in abstract_machine_stacks:
            definition_id = abstract_machine.definition.getId()
            from cura.CuraApplication import CuraApplication
            machines_manager = CuraApplication.getInstance().getMachineManager()
            online_machine_stacks = machines_manager.getMachinesWithDefinition(definition_id, online_only = True)

            def online_machines_has_connection_filter(machine_stack):
                # This is required because machines loaded from projects have the is_online="True" but no connection type.
                # We want to display them the same way as unconnected printers in this case.
                has_connection = False
                for connection_type in [ConnectionType.NetworkConnection.value, ConnectionType.CloudConnection.value]:
                    has_connection |= connection_type in machine_stack.configuredConnectionTypes
                return has_connection

            online_machine_stacks = list(filter(online_machines_has_connection_filter, online_machine_stacks))

            other_machine_stacks.remove(abstract_machine)
            if abstract_machine in online_machine_stacks:
                online_machine_stacks.remove(abstract_machine)

            # Create a list item for abstract machine
            self.addItem(abstract_machine, True, len(online_machine_stacks))

            # Create list of machines that are children of the abstract machine
            for stack in online_machine_stacks:
                if self._show_cloud_printers:
                    self.addItem(stack, True)
                # Remove this machine from the other stack list
                if stack in other_machine_stacks:
                    other_machine_stacks.remove(stack)

        if len(abstract_machine_stacks) > 0:
            if self._show_cloud_printers:
                self.appendItem({"componentType": "HIDE_BUTTON",
                                 "isOnline": True,
                                 "isAbstractMachine": False,
                                 "machineCount": 0
                                 })
            else:
                self.appendItem({"componentType": "SHOW_BUTTON",
                                 "isOnline": True,
                                 "isAbstractMachine": False,
                                 "machineCount": 0
                                 })

        for stack in other_machine_stacks:
            self.addItem(stack, False)

    def addItem(self, container_stack: ContainerStack, is_online: bool, machine_count: int = 0) -> None:
        if parseBool(container_stack.getMetaDataEntry("hidden", False)):
            return

        self.appendItem({
                        "componentType": "MACHINE",
                        "name": container_stack.getName(),
                         "id": container_stack.getId(),
                         "metadata": container_stack.getMetaData().copy(),
                         "isOnline": is_online,
                         "isAbstractMachine": parseBool(container_stack.getMetaDataEntry("is_abstract_machine", False)),
                         "machineCount": machine_count,
                         })
