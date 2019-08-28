# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING
from PyQt5.QtCore import pyqtSlot, QObject, Qt

from UM.Logger import Logger
from UM.Qt.ListModel import ListModel

import cura.CuraApplication  # Imported this way to prevent circular imports.
from cura.Machines.ContainerTree import ContainerTree
from cura.Settings.cura_empty_instance_containers import empty_quality_changes_container

if TYPE_CHECKING:
    from cura.Machines.QualityChangesGroup import QualityChangesGroup

#
# This the QML model for the quality management page.
#
class QualityManagementModel(ListModel):
    NameRole = Qt.UserRole + 1
    IsReadOnlyRole = Qt.UserRole + 2
    QualityGroupRole = Qt.UserRole + 3
    QualityChangesGroupRole = Qt.UserRole + 4

    def __init__(self, parent = None):
        super().__init__(parent)

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.IsReadOnlyRole, "is_read_only")
        self.addRoleName(self.QualityGroupRole, "quality_group")
        self.addRoleName(self.QualityChangesGroupRole, "quality_changes_group")

        application = cura.CuraApplication.CuraApplication.getInstance()
        self._container_registry = application.getContainerRegistry()
        self._machine_manager = application.getMachineManager()
        self._extruder_manager = application.getExtruderManager()

        self._machine_manager.globalContainerChanged.connect(self._update)

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
        new_name = application.getContainerRegistry().uniqueName(new_name)
        for node in quality_changes_group.getAllNodes():
            container = node.container
            if container:
                container.setName(new_name)

        quality_changes_group.name = new_name

        application.getMachineManager().activeQualityChanged.emit()
        application.getMachineManager().activeQualityGroupChanged.emit()

        return new_name

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
        # Create quality group items
        for quality_group in quality_group_dict.values():
            if not quality_group.is_available:
                continue

            item = {"name": quality_group.name,
                    "is_read_only": True,
                    "quality_group": quality_group,
                    "quality_changes_group": None}
            item_list.append(item)
        # Sort by quality names
        item_list = sorted(item_list, key = lambda x: x["name"].upper())

        # Create quality_changes group items
        quality_changes_item_list = []
        for quality_changes_group in quality_changes_group_list:
            quality_group = quality_group_dict.get(quality_changes_group.quality_type)
            item = {"name": quality_changes_group.name,
                    "is_read_only": False,
                    "quality_group": quality_group,
                    "quality_changes_group": quality_changes_group}
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
