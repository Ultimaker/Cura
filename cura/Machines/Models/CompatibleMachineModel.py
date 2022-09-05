# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

# TODO?: documentation

from typing import Optional, Dict

from PyQt6.QtCore import Qt, QObject, pyqtSlot, pyqtProperty, pyqtSignal

from UM.Qt.ListModel import ListModel
from UM.Settings.ContainerStack import ContainerStack
from UM.i18n import i18nCatalog
from UM.Util import parseBool

from cura.Settings.CuraContainerRegistry import CuraContainerRegistry


class CompatibleMachineModel(ListModel):
    NameRole = Qt.ItemDataRole.UserRole + 1
    IdRole = Qt.ItemDataRole.UserRole + 2
    ExtrudersRole = Qt.ItemDataRole.UserRole + 3

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        self._filter_on_definition_id: Optional[str] = None

        self._catalog = i18nCatalog("cura")

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.IdRole, "id")
        self.addRoleName(self.ExtrudersRole, "extruders")

    filterChanged = pyqtSignal(str)

    @pyqtSlot(str)
    def setFilter(self, abstract_machine_id: str) -> None:
        # TODO??: defensive coding; check if machine is abstract & abort/log if not
        self._filter_on_definition_id = abstract_machine_id

        # Don't need a delayed update, since it's fire once on user click (either on 'print to cloud' or 'refresh').
        # So, no signals that could come in (too) quickly.
        self.filterChanged.emit(self._filter_on_definition_id)
        self._update()

    @pyqtProperty(str, fset=setFilter, notify=filterChanged)
    def filter(self) -> str:
        return self._filter_on_definition_id

    def _update(self) -> None:
        self.clear()
        if not self._filter_on_definition_id or self._filter_on_definition_id == "":
            # TODO?: log
            return

        from cura.CuraApplication import CuraApplication
        machine_manager = CuraApplication.getInstance().getMachineManager()
        compatible_machines = machine_manager.getMachinesWithDefinition(self._filter_on_definition_id, online_only = True)
        # TODO: Handle 0 compatible machines -> option to close window? Message in card? (remember  the design has a refresh button!)

        for container_stack in compatible_machines:
            if parseBool(container_stack.getMetaDataEntry("hidden", False)) or parseBool(container_stack.getMetaDataEntry("is_abstract_machine", False)):
                continue
            self.addItem(container_stack)

    def addItem(self, container_stack: ContainerStack) -> None:
        extruders = CuraContainerRegistry.getInstance().findContainerStacks(type="extruder_train", machine=container_stack.getId())
        self.appendItem({
                         "name": container_stack.getName(),
                         "id": container_stack.getId(),
                         "extruders": [self.getExtruderModel(extruder) for extruder in extruders]
                        })

    def getExtruderModel(self, extruders: ContainerStack) -> Dict:
        # Temp Dummy Data
        extruder_model = {
            "core": "AA 0.4",
            "materials": [{"name": "Ultimaker Blue", "color": "blue"}, {"name": "Ultimaker Red", "color": "red"}, {"name": "Ultimaker Orange", "color": "orange"}]
        }
        return extruder_model

