# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import os.path
import urllib

from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal, QUrl
from PyQt5.QtWidgets import QMessageBox

import UM.PluginRegistry
import UM.Settings
import UM.SaveFile
import UM.Platform
import UM.MimeTypeDatabase
import UM.Logger

from UM.MimeTypeDatabase import MimeTypeNotFoundError

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
            UM.Logger.log("w", "Could duplicate container %s because it was not found.", container_id)
            return ""

        container = containers[0]

        new_container = None
        new_name = self._registry.uniqueName(container.getName())
        # Only InstanceContainer has a duplicate method at the moment.
        # So fall back to serialize/deserialize when no duplicate method exists.
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
            UM.Logger.log("w", "Could rename container %s because it was not found.", container_id)
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
            UM.Logger.log("w", "Could remove container %s because it was not found.", container_id)
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
        containers = self._registry.findContainers(None, id = merge_into_id)
        if not containers:
            UM.Logger.log("w", "Could merge into container %s because it was not found.", merge_into_id)
            return False

        merge_into = containers[0]

        containers = self._registry.findContainers(None, id = merge_id)
        if not containers:
            UM.Logger.log("w", "Could not merge container %s because it was not found", merge_id)
            return False

        merge = containers[0]

        if type(merge) != type(merge_into):
            UM.Logger.log("w", "Cannot merge two containers of different types")
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
            UM.Logger.log("w", "Could clear container %s because it was not found.", container_id)
            return False

        if containers[0].isReadOnly():
            UM.Logger.log("w", "Cannot clear read-only container %s", container_id)
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
            UM.Logger.log("w", "Could set metadata of container %s because it was not found.", container_id)
            return False

        container = containers[0]

        if container.isReadOnly():
            UM.Logger.log("w", "Cannot set metadata of read-only container %s.", container_id)
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

        container.setMetaDataEntry(entry_name, entry_value)

        return True

    ##  Find instance containers matching certain criteria.
    #
    #   This effectively forwards to ContainerRegistry::findInstanceContainers.
    #
    #   \param criteria A dict of key - value pairs to search for.
    #
    #   \return A list of container IDs that match the given criteria.
    @pyqtSlot("QVariantMap", result = "QVariantList")
    def findInstanceContainers(self, criteria):
        result = []
        for entry in self._registry.findInstanceContainers(**criteria):
            result.append(entry.getId())

        return result

    ##  Get a list of string that can be used as name filters for a Qt File Dialog
    #
    #   This will go through the list of available container types and generate a list of strings
    #   out of that. The strings are formatted as "description (*.extension)" and can be directly
    #   passed to a nameFilters property of a Qt File Dialog.
    #
    #   \param type_name Which types of containers to list. These types correspond to the "type"
    #                    key of the plugin metadata.
    #
    #   \return A string list with name filters.
    @pyqtSlot(str, result = "QStringList")
    def getContainerNameFilters(self, type_name):
        if not self._container_name_filters:
            self._updateContainerNameFilters()

        filters = []
        for filter_string, entry in self._container_name_filters.items():
            if not type_name or entry["type"] == type_name:
                filters.append(filter_string)

        filters.append("All Files (*)")
        return filters

    ##  Export a container to a file
    #
    #   \param container_id The ID of the container to export
    #   \param file_type The type of file to save as. Should be in the form of "description (*.extension, *.ext)"
    #   \param file_url The URL where to save the file.
    #
    #   \return A dictionary containing a key "status" with a status code and a key "message" with a message
    #           explaining the status.
    #           The status code can be one of "error", "cancelled", "success"
    @pyqtSlot(str, str, QUrl, result = "QVariantMap")
    def exportContainer(self, container_id, file_type, file_url):
        if not container_id or not file_type or not file_url:
            return { "status": "error", "message": "Invalid arguments"}

        if isinstance(file_url, QUrl):
            file_url = file_url.toLocalFile()

        if not file_url:
            return { "status": "error", "message": "Invalid path"}

        mime_type = None
        if not file_type in self._container_name_filters:
            try:
                mime_type = UM.MimeTypeDatabase.getMimeTypeForFile(file_url)
            except MimeTypeNotFoundError:
                return { "status": "error", "message": "Unknown File Type" }
        else:
            mime_type = self._container_name_filters[file_type]["mime"]

        containers = UM.Settings.ContainerRegistry.getInstance().findContainers(None, id = container_id)
        if not containers:
            return { "status": "error", "message": "Container not found"}
        container = containers[0]

        if UM.Platform.isOSX() and "." in file_url:
            file_url = file_url[:file_url.rfind(".")]

        for suffix in mime_type.suffixes:
            if file_url.endswith(suffix):
                break
        else:
            file_url += "." + mime_type.preferredSuffix

        if not UM.Platform.isWindows():
            if os.path.exists(file_url):
                result = QMessageBox.question(None, catalog.i18nc("@title:window", "File Already Exists"),
                                              catalog.i18nc("@label", "The file <filename>{0}</filename> already exists. Are you sure you want to overwrite it?").format(file_url))
                if result == QMessageBox.No:
                    return { "status": "cancelled", "message": "User cancelled"}

        try:
            contents = container.serialize()
        except NotImplementedError:
            return { "status": "error", "message": "Unable to serialize container"}

        with UM.SaveFile(file_url, "w") as f:
            f.write(contents)

        return { "status": "success", "message": "Succesfully exported container", "path": file_url}

    ##  Imports a profile from a file
    #
    #   \param file_url A URL that points to the file to import.
    #
    #   \return \type{Dict} dict with a 'status' key containing the string 'success' or 'error', and a 'message' key
    #       containing a message for the user
    @pyqtSlot(QUrl, result = "QVariantMap")
    def importContainer(self, file_url):
        if not file_url:
            return { "status": "error", "message": "Invalid path"}

        if isinstance(file_url, QUrl):
            file_url = file_url.toLocalFile()

        if not file_url or not os.path.exists(file_url):
            return { "status": "error", "message": "Invalid path" }

        try:
            mime_type = UM.MimeTypeDatabase.getMimeTypeForFile(file_url)
        except MimeTypeNotFoundError:
            return { "status": "error", "message": "Could not determine mime type of file" }

        container_type = UM.Settings.ContainerRegistry.getContainerForMimeType(mime_type)
        if not container_type:
            return { "status": "error", "message": "Could not find a container to handle the specified file."}

        container_id = urllib.parse.unquote_plus(mime_type.stripExtension(os.path.basename(file_url)))
        container_id = UM.Settings.ContainerRegistry.getInstance().uniqueName(container_id)

        container = container_type(container_id)

        try:
            with open(file_url, "rt") as f:
                container.deserialize(f.read())
        except PermissionError:
            return { "status": "error", "message": "Permission denied when trying to read the file"}

        container.setName(container_id)

        UM.Settings.ContainerRegistry.getInstance().addContainer(container)

        return { "status": "success", "message": "Successfully imported container {0}".format(container.getName()) }

    def _updateContainerNameFilters(self):
        self._container_name_filters = {}
        for plugin_id, container_type in UM.Settings.ContainerRegistry.getContainerTypes():
            # Ignore default container types since those are not plugins
            if container_type in (UM.Settings.InstanceContainer, UM.Settings.ContainerStack, UM.Settings.DefinitionContainer):
                continue

            serialize_type = ""
            try:
                plugin_metadata = UM.PluginRegistry.getInstance().getMetaData(plugin_id)
                if plugin_metadata:
                    serialize_type = plugin_metadata["settings_container"]["type"]
                else:
                    continue
            except KeyError as e:
                continue

            mime_type = UM.Settings.ContainerRegistry.getMimeTypeForContainer(container_type)

            entry = {
                "type": serialize_type,
                "mime": mime_type,
                "container": container_type
            }

            suffix = mime_type.preferredSuffix
            if UM.Platform.isOSX() and "." in suffix:
                # OSX's File dialog is stupid and does not allow selecting files with a . in its name
                suffix = suffix[suffix.index(".") + 1:]

            suffix_list = "*." + suffix
            for suffix in mime_type.suffixes:
                if suffix == mime_type.preferredSuffix:
                    continue

                if UM.Platform.isOSX() and "." in suffix:
                    # OSX's File dialog is stupid and does not allow selecting files with a . in its name
                    suffix = suffix[suffix.index("."):]

                suffix_list += ", *." + suffix

            name_filter = "{0} ({1})".format(mime_type.comment, suffix_list)
            self._container_name_filters[name_filter] = entry

    # Factory function, used by QML
    @staticmethod
    def createContainerManager(engine, js_engine):
        return ContainerManager()
