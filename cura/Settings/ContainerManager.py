# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal

import UM.Settings

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

class ContainerManager(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)

        self._registry = UM.Settings.ContainerRegistry.getInstance()

    @pyqtSlot(str)
    def duplicateContainer(self, container_id):
        containers = self._registry.findInstanceContainers(id = container_id)
        if not containers:
            return

        new_name = self_registry.uniqueName(containers[0].getName())
        new_material = containers[0].duplicate(new_name)
        self._registry.addContainer(new_material)

    @pyqtSlot(str, str)
    def renameContainer(self, container_id, new_name):
        pass

    @pyqtSlot(str)
    def removeContainer(self, container_id):
        pass

    @pyqtSlot(str, str, str)
    def setContainerMetaDataEntry(self, container_id, entry_name, entry_value):
        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = container_id)
        if not containers:
            return

        container = containers[0]

        entries = entry_name.split("/")
        entry_name = entries.pop()

        if entries:
            root_name = entries.pop(0)
            root = container.getMetaDataEntry(root_name)

            item = root
            for entry in entries:
                item = item.get(entries.pop(0), { })

            item[entry_name] = entry_value

            entry_name = root_name
            entry_value = root

        containers[0].setMetaDataEntry(entry_name, entry_value)

    @staticmethod
    def createContainerManager(engine, js_engine):
        return ContainerManager()
