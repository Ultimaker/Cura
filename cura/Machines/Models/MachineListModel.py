# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt6.QtCore import Qt, QTimer

from UM.Qt.ListModel import ListModel
from UM.Settings.ContainerStack import ContainerStack
from UM.i18n import i18nCatalog
from UM.Util import parseBool

from cura.Settings.CuraContainerRegistry import CuraContainerRegistry
from cura.Settings.GlobalStack import GlobalStack


class MachineListModel(ListModel):
    NameRole = Qt.ItemDataRole.UserRole + 1
    IdRole = Qt.ItemDataRole.UserRole + 2
    HasRemoteConnectionRole = Qt.ItemDataRole.UserRole + 3
    MetaDataRole = Qt.ItemDataRole.UserRole + 4
    IsOnlineRole = Qt.ItemDataRole.UserRole + 5
    MachineCountRole = Qt.ItemDataRole.UserRole + 6
    IsAbstractMachine = Qt.ItemDataRole.UserRole + 7

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._catalog = i18nCatalog("cura")

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.IdRole, "id")
        self.addRoleName(self.HasRemoteConnectionRole, "hasRemoteConnection")
        self.addRoleName(self.MetaDataRole, "metadata")
        self.addRoleName(self.IsOnlineRole, "isOnline")
        self.addRoleName(self.MachineCountRole, "machineCount")
        self.addRoleName(self.IsAbstractMachine, "isAbstractMachine")

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
        self.setItems([])  # Clear items

        other_machine_stacks = CuraContainerRegistry.getInstance().findContainerStacks(type="machine")

        abstract_machine_stacks = CuraContainerRegistry.getInstance().findContainerStacks(is_abstract_machine = "True")
        abstract_machine_stacks.sort(key = lambda machine: machine.getName(), reverse = True)

        for abstract_machine in abstract_machine_stacks:
            definition_id = abstract_machine.definition.getId()
            from cura.CuraApplication import CuraApplication
            machines_manager = CuraApplication.getInstance().getMachineManager()
            online_machine_stacks = machines_manager.getMachinesWithDefinition(definition_id, online_only = True)

            # Create a list item for abstract machine
            self.addItem(abstract_machine, len(online_machine_stacks))
            other_machine_stacks.remove(abstract_machine)

            # Create list of machines that are children of the abstract machine
            for stack in online_machine_stacks:
                self.addItem(stack)
                # Remove this machine from the other stack list
                other_machine_stacks.remove(stack)

        for stack in other_machine_stacks:
            self.addItem(stack)

    def addItem(self, container_stack: ContainerStack, machine_count: int = 0) -> None:
        if parseBool(container_stack.getMetaDataEntry("hidden", False)):
            return

        self.appendItem({"name": container_stack.getName(),
                         "id": container_stack.getId(),
                         "metadata": container_stack.getMetaData().copy(),
                         "isOnline": parseBool(container_stack.getMetaDataEntry("is_online", False)),
                         "isAbstractMachine": parseBool(container_stack.getMetaDataEntry("is_abstract_machine", False)),
                         "machineCount": machine_count,
                         })
