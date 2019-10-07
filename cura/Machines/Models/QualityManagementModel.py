# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, cast, Dict, Optional, TYPE_CHECKING
from PyQt5.QtCore import pyqtSlot, QObject, Qt

from UM.Logger import Logger
from UM.Qt.ListModel import ListModel
from UM.Settings.InstanceContainer import InstanceContainer  # To create new profiles.

import cura.CuraApplication  # Imported this way to prevent circular imports.
from cura.Settings.ContainerManager import ContainerManager
from cura.Machines.ContainerTree import ContainerTree
from cura.Settings.cura_empty_instance_containers import empty_quality_changes_container
from cura.Settings.IntentManager import IntentManager
from cura.Machines.Models.IntentCategoryModel import IntentCategoryModel

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

if TYPE_CHECKING:
    from UM.Settings.Interfaces import ContainerInterface
    from cura.Machines.QualityChangesGroup import QualityChangesGroup
    from cura.Settings.ExtruderStack import ExtruderStack
    from cura.Settings.GlobalStack import GlobalStack


#
# This the QML model for the quality management page.
#
class QualityManagementModel(ListModel):
    NameRole = Qt.UserRole + 1
    IsReadOnlyRole = Qt.UserRole + 2
    QualityGroupRole = Qt.UserRole + 3
    QualityTypeRole = Qt.UserRole + 4
    QualityChangesGroupRole = Qt.UserRole + 5
    IntentCategoryRole = Qt.UserRole + 6
    SectionNameRole = Qt.UserRole + 7

    def __init__(self, parent: Optional["QObject"] = None) -> None:
        super().__init__(parent)

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.IsReadOnlyRole, "is_read_only")
        self.addRoleName(self.QualityGroupRole, "quality_group")
        self.addRoleName(self.QualityTypeRole, "quality_type")
        self.addRoleName(self.QualityChangesGroupRole, "quality_changes_group")
        self.addRoleName(self.IntentCategoryRole, "intent_category")
        self.addRoleName(self.SectionNameRole, "section_name")

        application = cura.CuraApplication.CuraApplication.getInstance()
        container_registry = application.getContainerRegistry()
        self._machine_manager = application.getMachineManager()
        self._extruder_manager = application.getExtruderManager()

        self._machine_manager.globalContainerChanged.connect(self._update)
        container_registry.containerAdded.connect(self._qualityChangesListChanged)
        container_registry.containerRemoved.connect(self._qualityChangesListChanged)
        container_registry.containerMetaDataChanged.connect(self._qualityChangesListChanged)

        self._update()

    ##  Deletes a custom profile. It will be gone forever.
    #   \param quality_changes_group The quality changes group representing the
    #   profile to delete.
    @pyqtSlot(QObject)
    def removeQualityChangesGroup(self, quality_changes_group: "QualityChangesGroup") -> None:
        Logger.log("i", "Removing quality changes group {group_name}".format(group_name = quality_changes_group.name))
        removed_quality_changes_ids = set()
        container_registry = cura.CuraApplication.CuraApplication.getInstance().getContainerRegistry()
        for metadata in [quality_changes_group.metadata_for_global] + list(quality_changes_group.metadata_per_extruder.values()):
            container_id = metadata["id"]
            container_registry.removeContainer(container_id)
            removed_quality_changes_ids.add(container_id)

        # Reset all machines that have activated this custom profile.
        for global_stack in container_registry.findContainerStacks(type = "machine"):
            if global_stack.qualityChanges.getId() in removed_quality_changes_ids:
                global_stack.qualityChanges = empty_quality_changes_container
        for extruder_stack in container_registry.findContainerStacks(type = "extruder_train"):
            if extruder_stack.qualityChanges.getId() in removed_quality_changes_ids:
                extruder_stack.qualityChanges = empty_quality_changes_container

    ##  Rename a custom profile.
    #
    #   Because the names must be unique, the new name may not actually become
    #   the name that was given. The actual name is returned by this function.
    #   \param quality_changes_group The custom profile that must be renamed.
    #   \param new_name The desired name for the profile.
    #   \return The actual new name of the profile, after making the name
    #   unique.
    @pyqtSlot(QObject, str, result = str)
    def renameQualityChangesGroup(self, quality_changes_group: "QualityChangesGroup", new_name: str) -> str:
        Logger.log("i", "Renaming QualityChangesGroup {old_name} to {new_name}.".format(old_name = quality_changes_group.name, new_name = new_name))
        if new_name == quality_changes_group.name:
            Logger.log("i", "QualityChangesGroup name {name} unchanged.".format(name = quality_changes_group.name))
            return new_name

        application = cura.CuraApplication.CuraApplication.getInstance()
        container_registry = application.getContainerRegistry()
        new_name = container_registry.uniqueName(new_name)
        # CURA-6842
        # FIXME: setName() will trigger metaDataChanged signal that are connected with type Qt.AutoConnection. In this
        # case, setName() will trigger direct connections which in turn causes the quality changes group and the models
        # to update. Because multiple containers need to be renamed, and every time a container gets renamed, updates
        # gets triggered and this results in partial updates. For example, if we rename the global quality changes
        # container first, the rest of the system still thinks that I have selected "my_profile" instead of
        # "my_new_profile", but an update already gets triggered, and the quality changes group that's selected will
        # have no container for the global stack, because "my_profile" just got renamed to "my_new_profile". This results
        # in crashes because the rest of the system assumes that all data in a QualityChangesGroup will be correct.
        #
        # Renaming the container for the global stack in the end seems to be ok, because the assumption is mostly based
        # on the quality changes container for the global stack.
        for metadata in quality_changes_group.metadata_per_extruder.values():
            extruder_container = cast(InstanceContainer, container_registry.findContainers(id = metadata["id"])[0])
            extruder_container.setName(new_name)
        global_container = cast(InstanceContainer, container_registry.findContainers(id=quality_changes_group.metadata_for_global["id"])[0])
        global_container.setName(new_name)

        quality_changes_group.name = new_name

        application.getMachineManager().activeQualityChanged.emit()
        application.getMachineManager().activeQualityGroupChanged.emit()

        return new_name

    ##  Duplicates a given quality profile OR quality changes profile.
    #   \param new_name The desired name of the new profile. This will be made
    #   unique, so it might end up with a different name.
    #   \param quality_model_item The item of this model to duplicate, as
    #   dictionary. See the descriptions of the roles of this list model.
    @pyqtSlot(str, "QVariantMap")
    def duplicateQualityChanges(self, new_name: str, quality_model_item: Dict[str, Any]) -> None:
        global_stack = cura.CuraApplication.CuraApplication.getInstance().getGlobalContainerStack()
        if not global_stack:
            Logger.log("i", "No active global stack, cannot duplicate quality (changes) profile.")
            return

        container_registry = cura.CuraApplication.CuraApplication.getInstance().getContainerRegistry()
        new_name = container_registry.uniqueName(new_name)

        intent_category = quality_model_item["intent_category"]
        quality_group = quality_model_item["quality_group"]
        quality_changes_group = quality_model_item["quality_changes_group"]
        if quality_changes_group is None:
            # Create global quality changes only.
            new_quality_changes = self._createQualityChanges(quality_group.quality_type, intent_category, new_name,
                                                             global_stack, extruder_stack = None)
            container_registry.addContainer(new_quality_changes)
        else:
            for metadata in [quality_changes_group.metadata_for_global] + list(quality_changes_group.metadata_per_extruder.values()):
                containers = container_registry.findContainers(id = metadata["id"])
                if not containers:
                    continue
                container = containers[0]
                new_id = container_registry.uniqueName(container.getId())
                container_registry.addContainer(container.duplicate(new_id, new_name))

    ##  Create quality changes containers from the user containers in the active
    #   stacks.
    #
    #   This will go through the global and extruder stacks and create
    #   quality_changes containers from the user containers in each stack. These
    #   then replace the quality_changes containers in the stack and clear the
    #   user settings.
    #   \param base_name The new name for the quality changes profile. The final
    #   name of the profile might be different from this, because it needs to be
    #   made unique.
    @pyqtSlot(str)
    def createQualityChanges(self, base_name: str) -> None:
        machine_manager = cura.CuraApplication.CuraApplication.getInstance().getMachineManager()

        global_stack = machine_manager.activeMachine
        if not global_stack:
            return

        active_quality_name = machine_manager.activeQualityOrQualityChangesName
        if active_quality_name == "":
            Logger.log("w", "No quality container found in stack %s, cannot create profile", global_stack.getId())
            return

        machine_manager.blurSettings.emit()
        if base_name is None or base_name == "":
            base_name = active_quality_name
        container_registry = cura.CuraApplication.CuraApplication.getInstance().getContainerRegistry()
        unique_name = container_registry.uniqueName(base_name)

        # Go through the active stacks and create quality_changes containers from the user containers.
        container_manager = ContainerManager.getInstance()
        stack_list = [global_stack] + list(global_stack.extruders.values())
        for stack in stack_list:
            quality_container = stack.quality
            quality_changes_container = stack.qualityChanges
            if not quality_container or not quality_changes_container:
                Logger.log("w", "No quality or quality changes container found in stack %s, ignoring it", stack.getId())
                continue

            extruder_stack = None
            intent_category = None
            if stack.getMetaDataEntry("position") is not None:
                extruder_stack = stack
                intent_category = stack.intent.getMetaDataEntry("intent_category")
            new_changes = self._createQualityChanges(quality_container.getMetaDataEntry("quality_type"), intent_category, unique_name, global_stack, extruder_stack)
            container_manager._performMerge(new_changes, quality_changes_container, clear_settings = False)
            container_manager._performMerge(new_changes, stack.userChanges)

            container_registry.addContainer(new_changes)

    ##  Create a quality changes container with the given set-up.
    #   \param quality_type The quality type of the new container.
    #   \param intent_category The intent category of the new container.
    #   \param new_name The name of the container. This name must be unique.
    #   \param machine The global stack to create the profile for.
    #   \param extruder_stack The extruder stack to create the profile for. If
    #   not provided, only a global container will be created.
    def _createQualityChanges(self, quality_type: str, intent_category: Optional[str], new_name: str, machine: "GlobalStack", extruder_stack: Optional["ExtruderStack"]) -> "InstanceContainer":
        container_registry = cura.CuraApplication.CuraApplication.getInstance().getContainerRegistry()
        base_id = machine.definition.getId() if extruder_stack is None else extruder_stack.getId()
        new_id = base_id + "_" + new_name
        new_id = new_id.lower().replace(" ", "_")
        new_id = container_registry.uniqueName(new_id)

        # Create a new quality_changes container for the quality.
        quality_changes = InstanceContainer(new_id)
        quality_changes.setName(new_name)
        quality_changes.setMetaDataEntry("type", "quality_changes")
        quality_changes.setMetaDataEntry("quality_type", quality_type)
        if intent_category is not None:
            quality_changes.setMetaDataEntry("intent_category", intent_category)

        # If we are creating a container for an extruder, ensure we add that to the container.
        if extruder_stack is not None:
            quality_changes.setMetaDataEntry("position", extruder_stack.getMetaDataEntry("position"))

        # If the machine specifies qualities should be filtered, ensure we match the current criteria.
        machine_definition_id = ContainerTree.getInstance().machines[machine.definition.getId()].quality_definition
        quality_changes.setDefinition(machine_definition_id)

        quality_changes.setMetaDataEntry("setting_version", cura.CuraApplication.CuraApplication.getInstance().SettingVersion)
        return quality_changes

    ##  Triggered when any container changed.
    #
    #   This filters the updates to the container manager: When it applies to
    #   the list of quality changes, we need to update our list.
    def _qualityChangesListChanged(self, container: "ContainerInterface") -> None:
        if container.getMetaDataEntry("type") == "quality_changes":
            self._update()

    @pyqtSlot("QVariantMap", result = str)
    def getQualityItemDisplayName(self, quality_model_item: Dict[str, Any]) -> str:
        display_name = quality_model_item["name"]

        quality_group = quality_model_item["quality_group"]
        is_read_only = quality_model_item["is_read_only"]
        intent_category = quality_model_item["intent_category"]

        # Not a custom quality
        if is_read_only:
            return display_name

        # A custom quality
        if intent_category != "default":
            from cura.Machines.Models.IntentCategoryModel import IntentCategoryModel
            intent_display_name = catalog.i18nc("@label", intent_category.capitalize())
            display_name += " - {intent_name}".format(intent_name = intent_display_name)

        quality_level_name = "Not Supported"
        if quality_group is not None:
            quality_level_name = quality_group.name
        display_name += " - {quality_level_name}".format(quality_level_name = quality_level_name)
        return display_name

    def _update(self):
        Logger.log("d", "Updating {model_class_name}.".format(model_class_name = self.__class__.__name__))

        global_stack = self._machine_manager.activeMachine
        if not global_stack:
            self.setItems([])
            return

        container_tree = ContainerTree.getInstance()
        quality_group_dict = container_tree.getCurrentQualityGroups()
        quality_changes_group_list = container_tree.getCurrentQualityChangesGroups()

        available_quality_types = set(quality_type for quality_type, quality_group in quality_group_dict.items()
                                      if quality_group.is_available)
        if not available_quality_types and not quality_changes_group_list:
            # Nothing to show
            self.setItems([])
            return

        item_list = []
        # Create quality group items (intent category = "default")
        for quality_group in quality_group_dict.values():
            if not quality_group.is_available:
                continue

            item = {"name": quality_group.name,
                    "is_read_only": True,
                    "quality_group": quality_group,
                    "quality_type": quality_group.quality_type,
                    "quality_changes_group": None,
                    "intent_category": "default",
                    "section_name": catalog.i18nc("@label", "Default"),
                    }
            item_list.append(item)
        # Sort by quality names
        item_list = sorted(item_list, key = lambda x: x["name"].upper())

        # Create intent items (non-default)
        available_intent_list = IntentManager.getInstance().getCurrentAvailableIntents()
        available_intent_list = [i for i in available_intent_list if i[0] != "default"]
        result = []
        for intent_category, quality_type in available_intent_list:
            result.append({
                "name": quality_group_dict[quality_type].name,  # Use the quality name as the display name
                "is_read_only": True,
                "quality_group": quality_group_dict[quality_type],
                "quality_type": quality_type,
                "quality_changes_group": None,
                "intent_category": intent_category,
                "section_name": catalog.i18nc("@label", intent_category.capitalize()),
            })
        # Sort by quality_type for each intent category
        result = sorted(result, key = lambda x: (x["intent_category"], x["quality_type"]))
        item_list += result

        # Create quality_changes group items
        quality_changes_item_list = []
        for quality_changes_group in quality_changes_group_list:
            quality_group = quality_group_dict.get(quality_changes_group.quality_type)
            item = {"name": quality_changes_group.name,
                    "is_read_only": False,
                    "quality_group": quality_group,
                    "quality_type": quality_group.quality_type,
                    "quality_changes_group": quality_changes_group,
                    "intent_category": quality_changes_group.intent_category,
                    "section_name": catalog.i18nc("@label", "Custom profiles"),
                    }
            quality_changes_item_list.append(item)

        # Sort quality_changes items by names and append to the item list
        quality_changes_item_list = sorted(quality_changes_item_list, key = lambda x: x["name"].upper())
        item_list += quality_changes_item_list

        self.setItems(item_list)

    # TODO: Duplicated code here from InstanceContainersModel. Refactor and remove this later.
    #
    ##  Gets a list of the possible file filters that the plugins have
    #   registered they can read or write. The convenience meta-filters
    #   "All Supported Types" and "All Files" are added when listing
    #   readers, but not when listing writers.
    #
    #   \param io_type \type{str} name of the needed IO type
    #   \return A list of strings indicating file name filters for a file
    #   dialog.
    @pyqtSlot(str, result = "QVariantList")
    def getFileNameFilters(self, io_type):
        from UM.i18n import i18nCatalog
        catalog = i18nCatalog("uranium")
        #TODO: This function should be in UM.Resources!
        filters = []
        all_types = []
        for plugin_id, meta_data in self._getIOPlugins(io_type):
            for io_plugin in meta_data[io_type]:
                filters.append(io_plugin["description"] + " (*." + io_plugin["extension"] + ")")
                all_types.append("*.{0}".format(io_plugin["extension"]))

        if "_reader" in io_type:
            # if we're listing readers, add the option to show all supported files as the default option
            filters.insert(0, catalog.i18nc("@item:inlistbox", "All Supported Types ({0})", " ".join(all_types)))
            filters.append(catalog.i18nc("@item:inlistbox", "All Files (*)"))  # Also allow arbitrary files, if the user so prefers.
        return filters

    ##  Gets a list of profile reader or writer plugins
    #   \return List of tuples of (plugin_id, meta_data).
    def _getIOPlugins(self, io_type):
        from UM.PluginRegistry import PluginRegistry
        pr = PluginRegistry.getInstance()
        active_plugin_ids = pr.getActivePlugins()

        result = []
        for plugin_id in active_plugin_ids:
            meta_data = pr.getMetaData(plugin_id)
            if io_type in meta_data:
                result.append( (plugin_id, meta_data) )
        return result
