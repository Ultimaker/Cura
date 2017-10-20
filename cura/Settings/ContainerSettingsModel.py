# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Application import Application
from UM.Qt.ListModel import ListModel

from PyQt5.QtCore import pyqtProperty, Qt, pyqtSignal, pyqtSlot, QUrl

from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.SettingFunction import SettingFunction

class ContainerSettingsModel(ListModel):
    LabelRole = Qt.UserRole + 1
    CategoryRole = Qt.UserRole + 2
    UnitRole = Qt.UserRole + 3
    ValuesRole = Qt.UserRole + 4

    def __init__(self, parent = None):
        super().__init__(parent)
        self.addRoleName(self.LabelRole, "label")
        self.addRoleName(self.CategoryRole, "category")
        self.addRoleName(self.UnitRole, "unit")
        self.addRoleName(self.ValuesRole, "values")

        self._container_ids = []
        self._containers = []

    def _onPropertyChanged(self, key, property_name):
        if property_name == "value":
            self._update()

    def _update(self):
        items = []

        if len(self._container_ids) == 0:
            return

        keys = []
        for container in self._containers:
            keys = keys + list(container.getAllKeys())

        keys = list(set(keys)) # remove duplicate keys

        for key in keys:
            definition = None
            category = None
            values = []
            for container in self._containers:
                instance = container.getInstance(key)
                if instance:
                    definition = instance.definition

                    # Traverse up to find the category
                    category = definition
                    while category.type != "category":
                        category = category.parent

                    value = container.getProperty(key, "value")
                    if type(value) == SettingFunction:
                        values.append("=\u0192")
                    else:
                        values.append(container.getProperty(key, "value"))
                else:
                    values.append("")

            items.append({
                "key": key,
                "values": values,
                "label": definition.label,
                "unit": definition.unit,
                "category": category.label
            })
        items.sort(key = lambda k: (k["category"], k["key"]))
        self.setItems(items)

    ##  Set the ids of the containers which have the settings this model should list.
    #   Also makes sure the model updates when the containers have property changes
    def setContainers(self, container_ids):
        for container in self._containers:
            container.propertyChanged.disconnect(self._onPropertyChanged)

        self._container_ids = container_ids
        self._containers = []

        for container_id in self._container_ids:
            containers = ContainerRegistry.getInstance().findContainers(id = container_id)
            if containers:
                containers[0].propertyChanged.connect(self._onPropertyChanged)
                self._containers.append(containers[0])

        self._update()

    containersChanged = pyqtSignal()
    @pyqtProperty("QVariantList", fset = setContainers, notify = containersChanged)
    def containers(self):
        return self.container_ids
