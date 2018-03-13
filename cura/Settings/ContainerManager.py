# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os.path
import urllib.parse
import uuid
from typing import Dict, Union

from PyQt5.QtCore import QObject, QUrl, QVariant
from UM.FlameProfiler import pyqtSlot
from PyQt5.QtWidgets import QMessageBox

from UM.PluginRegistry import PluginRegistry
from UM.SaveFile import SaveFile
from UM.Platform import Platform
from UM.MimeTypeDatabase import MimeTypeDatabase

from UM.Logger import Logger
from UM.Application import Application
from UM.Settings.ContainerStack import ContainerStack
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.InstanceContainer import InstanceContainer

from UM.MimeTypeDatabase import MimeTypeNotFoundError
from UM.Settings.ContainerRegistry import ContainerRegistry

from UM.i18n import i18nCatalog

from cura.Settings.ExtruderManager import ExtruderManager
from cura.Settings.ExtruderStack import ExtruderStack

catalog = i18nCatalog("cura")


##  Manager class that contains common actions to deal with containers in Cura.
#
#   This is primarily intended as a class to be able to perform certain actions
#   from within QML. We want to be able to trigger things like removing a container
#   when a certain action happens. This can be done through this class.
class ContainerManager(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)

        self._application = Application.getInstance()
        self._container_registry = ContainerRegistry.getInstance()
        self._machine_manager = self._application.getMachineManager()
        self._material_manager = self._application.getMaterialManager()
        self._container_name_filters = {}

    @pyqtSlot(str, str, result=str)
    def getContainerMetaDataEntry(self, container_id, entry_name):
        metadatas = self._container_registry.findContainersMetadata(id = container_id)
        if not metadatas:
            Logger.log("w", "Could not get metadata of container %s because it was not found.", container_id)
            return ""

        return str(metadatas[0].get(entry_name, ""))

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
    #  TODO: This is ONLY used by MaterialView for material containers. Maybe refactor this.
    @pyqtSlot("QVariant", str, str)
    def setContainerMetaDataEntry(self, container_node, entry_name, entry_value):
        root_material_id = container_node.metadata["base_file"]
        if self._container_registry.isReadOnly(root_material_id):
            Logger.log("w", "Cannot set metadata of read-only container %s.", root_material_id)
            return False

        material_group = self._material_manager.getMaterialGroup(root_material_id)

        entries = entry_name.split("/")
        entry_name = entries.pop()

        sub_item_changed = False
        if entries:
            root_name = entries.pop(0)
            root = material_group.root_material_node.metadata.get(root_name)

            item = root
            for _ in range(len(entries)):
                item = item.get(entries.pop(0), { })

            if item[entry_name] != entry_value:
                sub_item_changed = True
            item[entry_name] = entry_value

            entry_name = root_name
            entry_value = root

        container = material_group.root_material_node.getContainer()
        container.setMetaDataEntry(entry_name, entry_value)
        if sub_item_changed: #If it was only a sub-item that has changed then the setMetaDataEntry won't correctly notice that something changed, and we must manually signal that the metadata changed.
            container.metaDataChanged.emit(container)

    ##  Set a setting property of the specified container.
    #
    #   This will set the specified property of the specified setting of the container
    #   and all containers that share the same base_file (if any). The latter only
    #   happens for material containers.
    #
    #   \param container_id \type{str} The ID of the container to change.
    #   \param setting_key \type{str} The key of the setting.
    #   \param property_name \type{str} The name of the property, eg "value".
    #   \param property_value \type{str} The new value of the property.
    #
    #   \return True if successful, False if not.
    @pyqtSlot(str, str, str, str, result = bool)
    def setContainerProperty(self, container_id, setting_key, property_name, property_value):
        if self._container_registry.isReadOnly(container_id):
            Logger.log("w", "Cannot set properties of read-only container %s.", container_id)
            return False

        containers = self._container_registry.findContainers(id = container_id)
        if not containers:
            Logger.log("w", "Could not set properties of container %s because it was not found.", container_id)
            return False

        container = containers[0]

        container.setProperty(setting_key, property_name, property_value)

        basefile = container.getMetaDataEntry("base_file", container_id)
        for sibbling_container in ContainerRegistry.getInstance().findInstanceContainers(base_file = basefile):
            if sibbling_container != container:
                sibbling_container.setProperty(setting_key, property_name, property_value)

        return True

    ##  Get a setting property of the specified container.
    #
    #   This will get the specified property of the specified setting of the
    #   specified container.
    #
    #   \param container_id The ID of the container to get the setting property
    #   of.
    #   \param setting_key The key of the setting to get the property of.
    #   \param property_name The property to obtain.
    #   \return The value of the specified property. The type of this property
    #   value depends on the type of the property. For instance, the "value"
    #   property of an integer setting will be a Python int, but the "value"
    #   property of an enum setting will be a Python str.
    @pyqtSlot(str, str, str, result = QVariant)
    def getContainerProperty(self, container_id: str, setting_key: str, property_name: str):
        containers = self._container_registry.findContainers(id = container_id)
        if not containers:
            Logger.log("w", "Could not get properties of container %s because it was not found.", container_id)
            return ""
        container = containers[0]

        return container.getProperty(setting_key, property_name)

    @pyqtSlot(str, result = str)
    def makeUniqueName(self, original_name):
        return self._container_registry.uniqueName(original_name)

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
    #   \param file_url_or_string The URL where to save the file.
    #
    #   \return A dictionary containing a key "status" with a status code and a key "message" with a message
    #           explaining the status.
    #           The status code can be one of "error", "cancelled", "success"
    @pyqtSlot(str, str, QUrl, result = "QVariantMap")
    def exportContainer(self, container_id: str, file_type: str, file_url_or_string: Union[QUrl, str]) -> Dict[str, str]:
        if not container_id or not file_type or not file_url_or_string:
            return {"status": "error", "message": "Invalid arguments"}

        if isinstance(file_url_or_string, QUrl):
            file_url = file_url_or_string.toLocalFile()
        else:
            file_url = file_url_or_string

        if not file_url:
            return {"status": "error", "message": "Invalid path"}

        mime_type = None
        if file_type not in self._container_name_filters:
            try:
                mime_type = MimeTypeDatabase.getMimeTypeForFile(file_url)
            except MimeTypeNotFoundError:
                return {"status": "error", "message": "Unknown File Type"}
        else:
            mime_type = self._container_name_filters[file_type]["mime"]

        containers = self._container_registry.findContainers(id = container_id)
        if not containers:
            return {"status": "error", "message": "Container not found"}
        container = containers[0]

        if Platform.isOSX() and "." in file_url:
            file_url = file_url[:file_url.rfind(".")]

        for suffix in mime_type.suffixes:
            if file_url.endswith(suffix):
                break
        else:
            file_url += "." + mime_type.preferredSuffix

        if not Platform.isWindows():
            if os.path.exists(file_url):
                result = QMessageBox.question(None, catalog.i18nc("@title:window", "File Already Exists"),
                                              catalog.i18nc("@label Don't translate the XML tag <filename>!", "The file <filename>{0}</filename> already exists. Are you sure you want to overwrite it?").format(file_url))
                if result == QMessageBox.No:
                    return {"status": "cancelled", "message": "User cancelled"}

        try:
            contents = container.serialize()
        except NotImplementedError:
            return {"status": "error", "message": "Unable to serialize container"}

        if contents is None:
            return {"status": "error", "message": "Serialization returned None. Unable to write to file"}

        with SaveFile(file_url, "w") as f:
            f.write(contents)

        return {"status": "success", "message": "Successfully exported container", "path": file_url}

    ##  Imports a profile from a file
    #
    #   \param file_url A URL that points to the file to import.
    #
    #   \return \type{Dict} dict with a 'status' key containing the string 'success' or 'error', and a 'message' key
    #       containing a message for the user
    @pyqtSlot(QUrl, result = "QVariantMap")
    def importMaterialContainer(self, file_url_or_string: Union[QUrl, str]) -> Dict[str, str]:
        if not file_url_or_string:
            return {"status": "error", "message": "Invalid path"}

        if isinstance(file_url_or_string, QUrl):
            file_url = file_url_or_string.toLocalFile()
        else:
            file_url = file_url_or_string

        if not file_url or not os.path.exists(file_url):
            return {"status": "error", "message": "Invalid path"}

        try:
            mime_type = MimeTypeDatabase.getMimeTypeForFile(file_url)
        except MimeTypeNotFoundError:
            return {"status": "error", "message": "Could not determine mime type of file"}

        container_type = self._container_registry.getContainerForMimeType(mime_type)
        if not container_type:
            return {"status": "error", "message": "Could not find a container to handle the specified file."}

        container_id = urllib.parse.unquote_plus(mime_type.stripExtension(os.path.basename(file_url)))
        container_id = self._container_registry.uniqueName(container_id)

        container = container_type(container_id)

        try:
            with open(file_url, "rt", encoding = "utf-8") as f:
                container.deserialize(f.read())
        except PermissionError:
            return {"status": "error", "message": "Permission denied when trying to read the file"}
        except Exception as ex:
            return {"status": "error", "message": str(ex)}

        container.setDirty(True)

        self._container_registry.addContainer(container)

        return {"status": "success", "message": "Successfully imported container {0}".format(container.getName())}

    ##  Update the current active quality changes container with the settings from the user container.
    #
    #   This will go through the active global stack and all active extruder stacks and merge the changes from the user
    #   container into the quality_changes container. After that, the user container is cleared.
    #
    #   \return \type{bool} True if successful, False if not.
    @pyqtSlot(result = bool)
    def updateQualityChanges(self):
        global_stack = Application.getInstance().getGlobalContainerStack()
        if not global_stack:
            return False

        self._machine_manager.blurSettings.emit()

        for stack in ExtruderManager.getInstance().getActiveGlobalAndExtruderStacks():
            # Find the quality_changes container for this stack and merge the contents of the top container into it.
            quality_changes = stack.qualityChanges
            if not quality_changes or self._container_registry.isReadOnly(quality_changes.getId()):
                Logger.log("e", "Could not update quality of a nonexistant or read only quality profile in stack %s", stack.getId())
                continue

            self._performMerge(quality_changes, stack.getTop())

        self._machine_manager.activeQualityChangesGroupChanged.emit()

        return True

    ##  Clear the top-most (user) containers of the active stacks.
    @pyqtSlot()
    def clearUserContainers(self) -> None:
        self._machine_manager.blurSettings.emit()

        send_emits_containers = []

        # Go through global and extruder stacks and clear their topmost container (the user settings).
        for stack in ExtruderManager.getInstance().getActiveGlobalAndExtruderStacks():
            container = stack.userChanges
            container.clear()
            send_emits_containers.append(container)

        # user changes are possibly added to make the current setup match the current enabled extruders
        Application.getInstance().getMachineManager().correctExtruderSettings()

        for container in send_emits_containers:
            container.sendPostponedEmits()

    ##  Get a list of materials that have the same GUID as the reference material
    #
    #   \param material_id \type{str} the id of the material for which to get the linked materials.
    #   \return \type{list} a list of names of materials with the same GUID
    @pyqtSlot("QVariant", result = "QStringList")
    def getLinkedMaterials(self, material_node):
        guid = material_node.metadata["GUID"]

        material_group_list = self._material_manager.getMaterialGroupListByGUID(guid)

        linked_material_names = []
        if material_group_list:
            for material_group in material_group_list:
                linked_material_names.append(material_group.root_material_node.metadata["name"])
        return linked_material_names

    ##  Unlink a material from all other materials by creating a new GUID
    #   \param material_id \type{str} the id of the material to create a new GUID for.
    @pyqtSlot("QVariant")
    def unlinkMaterial(self, material_node):
        # Get the material group
        material_group = self._material_manager.getMaterialGroup(material_node.metadata["base_file"])

        # Generate a new GUID
        new_guid = str(uuid.uuid4())

        # Update the GUID
        # NOTE: We only need to set the root material container because XmlMaterialProfile.setMetaDataEntry() will
        # take care of the derived containers too
        container = material_group.root_material_node.getContainer()
        container.setMetaDataEntry("GUID", new_guid)

    ##  Get the singleton instance for this class.
    @classmethod
    def getInstance(cls) -> "ContainerManager":
        # Note: Explicit use of class name to prevent issues with inheritance.
        if ContainerManager.__instance is None:
            ContainerManager.__instance = cls()
        return ContainerManager.__instance

    __instance = None   # type: "ContainerManager"

    # Factory function, used by QML
    @staticmethod
    def createContainerManager(engine, js_engine):
        return ContainerManager.getInstance()

    def _performMerge(self, merge_into, merge, clear_settings = True):
        if merge == merge_into:
            return

        for key in merge.getAllKeys():
            merge_into.setProperty(key, "value", merge.getProperty(key, "value"))

        if clear_settings:
            merge.clear()

    def _updateContainerNameFilters(self) -> None:
        self._container_name_filters = {}
        for plugin_id, container_type in self._container_registry.getContainerTypes():
            # Ignore default container types since those are not plugins
            if container_type in (InstanceContainer, ContainerStack, DefinitionContainer):
                continue

            serialize_type = ""
            try:
                plugin_metadata = PluginRegistry.getInstance().getMetaData(plugin_id)
                if plugin_metadata:
                    serialize_type = plugin_metadata["settings_container"]["type"]
                else:
                    continue
            except KeyError as e:
                continue

            mime_type = self._container_registry.getMimeTypeForContainer(container_type)

            entry = {
                "type": serialize_type,
                "mime": mime_type,
                "container": container_type
            }

            suffix = mime_type.preferredSuffix
            if Platform.isOSX() and "." in suffix:
                # OSX's File dialog is stupid and does not allow selecting files with a . in its name
                suffix = suffix[suffix.index(".") + 1:]

            suffix_list = "*." + suffix
            for suffix in mime_type.suffixes:
                if suffix == mime_type.preferredSuffix:
                    continue

                if Platform.isOSX() and "." in suffix:
                    # OSX's File dialog is stupid and does not allow selecting files with a . in its name
                    suffix = suffix[suffix.index("."):]

                suffix_list += ", *." + suffix

            name_filter = "{0} ({1})".format(mime_type.comment, suffix_list)
            self._container_name_filters[name_filter] = entry

    ##  Import single profile, file_url does not have to end with curaprofile
    @pyqtSlot(QUrl, result="QVariantMap")
    def importProfile(self, file_url):
        if not file_url.isValid():
            return
        path = file_url.toLocalFile()
        if not path:
            return
        return self._container_registry.importProfile(path)

    @pyqtSlot(QObject, QUrl, str)
    def exportQualityChangesGroup(self, quality_changes_group, file_url: QUrl, file_type: str):
        if not file_url.isValid():
            return
        path = file_url.toLocalFile()
        if not path:
            return

        container_list = [n.getContainer() for n in quality_changes_group.getAllNodes()]
        self._container_registry.exportQualityProfile(container_list, path, file_type)
