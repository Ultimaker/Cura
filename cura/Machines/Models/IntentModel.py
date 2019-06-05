# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional
from PyQt5.QtCore import QObject
from UM.Qt.ListModel import ListModel
from PyQt5.QtCore import Qt

from UM.Settings.ContainerRegistry import ContainerRegistry


class IntentModel(ListModel):
    NameRole = Qt.UserRole + 1
    IdRole = Qt.UserRole + 2
    ContainerRole = Qt.UserRole + 3

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.IdRole, "id")
        self.addRoleName(self.ContainerRole, "container")

        ContainerRegistry.getInstance().containerAdded.connect(self._onChanged)
        ContainerRegistry.getInstance().containerRemoved.connect(self._onChanged)

        self._update()

    def _onChanged(self, container):
        if container.getMetaDataEntry("type") == "intent":
            self._update()

    def _update(self) -> None:
        new_items = []
        for container in ContainerRegistry.getInstance().findInstanceContainers(type="intent"):
            new_items.append({"name": container.getName(), "id": container.getId(), "container": container})

        self.setItems(new_items)
