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
        self._container_name_filters = {}

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
        containers = self._registry.findContainers(None, id = container_id)
        if not containers:
            return ""

        container = containers[0]

        new_container = None
        new_name = self._registry.uniqueName(container.getName())
        if hasattr(container, "duplicate"):
            new_container = container.duplicate(new_name)
        else:
            new_container = container.__class__(new_name)
            new_container.deserialize(container.serialize())
            new_container.setName(new_name)

        if new_container:
            self._registry.addContainer(new_container)

        return new_container.getId()

    ##  Change the name of a specified container to a new name.
    #
    #   \param container_id \type{str} The ID of the container to change the name of.
    #   \param new_id \type{str} The new ID of the container.
    #   \param new_name \type{str} The new name of the specified container.
    #
    #   \return True if successful, False if not.
    @pyqtSlot(str, str, str, result = bool)
    def renameContainer(self, container_id, new_id, new_name):
        containers = self._registry.findContainers(None, id = container_id)
        if not containers:
            return False

        container = containers[0]
        # First, remove the container from the registry. This will clean up any files related to the container.
        self._registry.removeContainer(container)

        # Ensure we have a unique name for the container
        new_name = self._registry.uniqueName(new_name)

        # Then, update the name and ID of the container
        container.setName(new_name)
        container._id = new_id # TODO: Find a nicer way to set a new, unique ID

        # Finally, re-add the container so it will be properly serialized again.
        self._registry.addContainer(container)

        return True

    ##  Remove the specified container.
    #
    #   \param container_id \type{str} The ID of the container to remove.
    #
    #   \return True if the container was successfully removed, False if not.
    @pyqtSlot(str, result = bool)
    def removeContainer(self, container_id):
        containers = self._registry.findContainers(None, id = container_id)
        if not containers:
            return False

        self._registry.removeContainer(containers[0].getId())

        return True

    ##  Merge a container with another.
    #
    #   This will try to merge one container into the other, by going through the container
    #   and setting the right properties on the other container.
    #
    #   \param merge_into_id \type{str} The ID of the container to merge into.
    #   \param merge_id \type{str} The ID of the container to merge.
    #
    #   \return True if successfully merged, False if not.
    @pyqtSlot(str, result = bool)
    def mergeContainers(self, merge_into_id, merge_id):
        containers = self._registry.findContainers(None, id = container_id)
        if not containers:
            return False

        merge_into = containers[0]

        containers = self._registry.findContainers(None, id = container_id)
        if not containers:
            return False

        merge = containers[0]

        if type(merge) != type(merge_into):
            return False

        for key in merge.getAllKeys():
            merge_into.setProperty(key, "value", merge.getProperty(key, "value"))

        return True

    ##  Clear the contents of a container.
    #
    #   \param container_id \type{str} The ID of the container to clear.
    #
    #   \return True if successful, False if not.
    @pyqtSlot(str, result = bool)
    def clearContainer(self, container_id):
        containers = self._registry.findContainers(None, id = container_id)
        if not containers:
            return False

        if containers[0].isReadOnly():
            return False

        containers[0].clear()

        return True

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
    #
    #   \return True if successful, False if not.
    @pyqtSlot(str, str, str, result = bool)
    def setContainerMetaDataEntry(self, container_id, entry_name, entry_value):
        containers = UM.Settings.ContainerRegistry.getInstance().findContainers(None, id = container_id)
        if not containers:
            return False

        container = containers[0]

        if container.isReadOnly():
            return False

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
