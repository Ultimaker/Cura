# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

# The MachineListModel is used to display the connected printers in the interface. Both the abstract machines and all
# online cloud connected printers are represented within this ListModel. Additional information such as the number of
# connected printers for each printer type is gathered.

from typing import Optional, List, cast, Dict, Any

from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSlot, pyqtProperty, pyqtSignal

from UM.Qt.ListModel import ListModel
from UM.Settings.ContainerStack import ContainerStack
from UM.Settings.Interfaces import ContainerInterface
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
    IsAbstractMachineRole = Qt.ItemDataRole.UserRole + 7
    ComponentTypeRole = Qt.ItemDataRole.UserRole + 8
    IsNetworkedMachineRole = Qt.ItemDataRole.UserRole + 9

    def __init__(self, parent: Optional[QObject] = None, machines_filter: List[GlobalStack] = None, listenToChanges: bool = True, showCloudPrinters: bool = False) -> None:
        super().__init__(parent)

        self._show_cloud_printers = showCloudPrinters
        self._machines_filter = machines_filter

        self._catalog = i18nCatalog("cura")

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.IdRole, "id")
        self.addRoleName(self.HasRemoteConnectionRole, "hasRemoteConnection")
        self.addRoleName(self.MetaDataRole, "metadata")
        self.addRoleName(self.IsOnlineRole, "isOnline")
        self.addRoleName(self.MachineCountRole, "machineCount")
        self.addRoleName(self.IsAbstractMachineRole, "isAbstractMachine")
        self.addRoleName(self.ComponentTypeRole, "componentType")
        self.addRoleName(self.IsNetworkedMachineRole, "isNetworked")

        self._change_timer = QTimer()
        self._change_timer.setInterval(200)
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self._update)

        if listenToChanges:
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

    def _onContainerChanged(self, container: ContainerInterface) -> None:
        """Handler for container added/removed events from registry"""

        # We only need to update when the added / removed container GlobalStack
        if isinstance(container, GlobalStack):
            self._updateDelayed()

    def _updateDelayed(self) -> None:
        self._change_timer.start()

    def _getMachineStacks(self) -> List[ContainerStack]:
        return CuraContainerRegistry.getInstance().findContainerStacks(type = "machine")

    def _getAbstractMachineStacks(self) -> List[ContainerStack]:
        return CuraContainerRegistry.getInstance().findContainerStacks(is_abstract_machine = "True")

    def set_machines_filter(self, machines_filter: Optional[List[GlobalStack]]) -> None:
        self._machines_filter = machines_filter
        self._update()

    def _update(self) -> None:
        self.clear()

        from cura.CuraApplication import CuraApplication
        machines_manager = CuraApplication.getInstance().getMachineManager()

        other_machine_stacks = self._getMachineStacks()
        other_machine_stacks.sort(key = lambda machine: machine.getName().upper())

        abstract_machine_stacks = self._getAbstractMachineStacks()
        abstract_machine_stacks.sort(key = lambda machine: machine.getName().upper(), reverse = True)

        if self._machines_filter is not None:
            filter_ids = [machine_filter.id for machine_filter in self._machines_filter]
            other_machine_stacks = [machine for machine in other_machine_stacks if machine.id in filter_ids]
            abstract_machine_stacks = [machine for machine in abstract_machine_stacks if machine.id in filter_ids]

        for abstract_machine in abstract_machine_stacks:
            definition_id = abstract_machine.definition.getId()
            connected_machine_stacks = machines_manager.getMachinesWithDefinition(definition_id, online_only = False)

            connected_machine_stacks = list(filter(lambda machine: machine.hasNetworkedConnection(), connected_machine_stacks))
            connected_machine_stacks.sort(key=lambda machine: machine.getName().upper())

            if abstract_machine in other_machine_stacks:
                other_machine_stacks.remove(abstract_machine)

            if abstract_machine in connected_machine_stacks:
                connected_machine_stacks.remove(abstract_machine)

            # Create a list item for abstract machine
            self.addItem(abstract_machine, True, len(connected_machine_stacks))

            # Create list of machines that are children of the abstract machine
            for stack in connected_machine_stacks:
                if self._show_cloud_printers:
                    self.addItem(stack, True)
                # Remove this machine from the other stack list
                if stack in other_machine_stacks:
                    other_machine_stacks.remove(stack)

        if len(abstract_machine_stacks) > 0:
            self.appendItem({
                "componentType": "HIDE_BUTTON" if self._show_cloud_printers else "SHOW_BUTTON",
                "isOnline": True,
                "isAbstractMachine": False,
                "machineCount": 0,
                "catergory": "connected",
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
            "isNetworked": cast(GlobalStack, container_stack).hasNetworkedConnection() if isinstance(container_stack, GlobalStack) else False,
            "machineCount": machine_count,
            "catergory": "connected" if is_online else "other",
        })

    def getItems(self) -> Dict[str, Any]:
        if self.count > 0:
            return self.items
        return {}