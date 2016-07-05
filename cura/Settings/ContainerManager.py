# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal

import UM.Settings

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

##  Manager class that contains common actions to deal with containers in Cura.
#
#   This is primarily intended as a class to be able to perform certain actions
#   from within QML. We want to be able to trigger things like removing a container
#   when a certain action happens. This can be done through this class.
class ContainerManager(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)

        self._registry = UM.Settings.ContainerRegistry.getInstance()

    ##  Create a duplicate of the specified container
    #
    #   This will create and add a duplicate of the container corresponding
    #   to the container ID.
    #
    #   \param container_id \type{str} The ID of the container to duplicate.
    #
    #   \return The ID of the new container, or an empty string if duplication failed.
    @pyqtSlot(str, result = str)
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

    ##  Set a metadata entry of the specified container.
    #
    #   This will set the specified entry of the container's metadata to the specified
    #   value. Note that entries containing dictionaries can have their entries changed
    #   by using "/" as a separator. For example, to change an entry "foo" in a
    #   dictionary entry "bar", you can specify "bar/foo" as entry name.
    #
    #   \param container_id \type{str} The ID of the container to change.
    #   \param entry_name \type{str} The name of the metadata entry to change.
    #   \param entry_value The new value of the entry.
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

    # Factory function, used by QML
    @staticmethod
    def createContainerManager(engine, js_engine):
        return ContainerManager()
