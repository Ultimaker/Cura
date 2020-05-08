# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty, pyqtSignal, Qt
from typing import Set

import cura.CuraApplication
from UM.Logger import Logger
from UM.Qt.ListModel import ListModel
from UM.Settings.ContainerRegistry import ContainerRegistry


class QualitySettingsModel(ListModel):
    """This model is used to show details settings of the selected quality in the quality management page."""

    KeyRole = Qt.UserRole + 1
    LabelRole = Qt.UserRole + 2
    UnitRole = Qt.UserRole + 3
    ProfileValueRole = Qt.UserRole + 4
    ProfileValueSourceRole = Qt.UserRole + 5
    UserValueRole = Qt.UserRole + 6
    CategoryRole = Qt.UserRole + 7

    GLOBAL_STACK_POSITION = -1

    def __init__(self, parent = None) -> None:
        super().__init__(parent = parent)

        self.addRoleName(self.KeyRole, "key")
        self.addRoleName(self.LabelRole, "label")
        self.addRoleName(self.UnitRole, "unit")
        self.addRoleName(self.ProfileValueRole, "profile_value")
        self.addRoleName(self.ProfileValueSourceRole, "profile_value_source")
        self.addRoleName(self.UserValueRole, "user_value")
        self.addRoleName(self.CategoryRole, "category")

        self._container_registry = ContainerRegistry.getInstance()
        self._application = cura.CuraApplication.CuraApplication.getInstance()
        self._application.getMachineManager().activeStackChanged.connect(self._update)

        # Must be either GLOBAL_STACK_POSITION or an extruder position (0, 1, etc.)
        self._selected_position = self.GLOBAL_STACK_POSITION

        self._selected_quality_item = None  # The selected quality in the quality management page
        self._i18n_catalog = None

        self._update()

    selectedPositionChanged = pyqtSignal()
    selectedQualityItemChanged = pyqtSignal()

    def setSelectedPosition(self, selected_position: int) -> None:
        if selected_position != self._selected_position:
            self._selected_position = selected_position
            self.selectedPositionChanged.emit()
            self._update()

    @pyqtProperty(int, fset = setSelectedPosition, notify = selectedPositionChanged)
    def selectedPosition(self) -> int:
        return self._selected_position

    def setSelectedQualityItem(self, selected_quality_item):
        if selected_quality_item != self._selected_quality_item:
            self._selected_quality_item = selected_quality_item
            self.selectedQualityItemChanged.emit()
            self._update()

    @pyqtProperty("QVariantMap", fset = setSelectedQualityItem, notify = selectedQualityItemChanged)
    def selectedQualityItem(self):
        return self._selected_quality_item

    def _update(self) -> None:
        Logger.log("d", "Updating {model_class_name}.".format(model_class_name = self.__class__.__name__))

        if not self._selected_quality_item:
            self.setItems([])
            return

        items = []

        global_container_stack = self._application.getGlobalContainerStack()
        definition_container = global_container_stack.definition

        quality_group = self._selected_quality_item["quality_group"]
        quality_changes_group = self._selected_quality_item["quality_changes_group"]

        quality_node = None
        settings_keys = set()  # type: Set[str]
        if quality_group:
            if self._selected_position == self.GLOBAL_STACK_POSITION:
                quality_node = quality_group.node_for_global
            else:
                quality_node = quality_group.nodes_for_extruders.get(str(self._selected_position))
            settings_keys = quality_group.getAllKeys()
        quality_containers = []
        if quality_node is not None and quality_node.container is not None:
            quality_containers.append(quality_node.container)

        # Here, if the user has selected a quality changes, then "quality_changes_group" will not be None, and we fetch
        # the settings in that quality_changes_group.
        if quality_changes_group is not None:
            container_registry = ContainerRegistry.getInstance()
            global_containers = container_registry.findContainers(id = quality_changes_group.metadata_for_global["id"])
            global_container = None if len(global_containers) == 0 else global_containers[0]
            extruders_containers = {pos: container_registry.findContainers(id = quality_changes_group.metadata_per_extruder[pos]["id"]) for pos in quality_changes_group.metadata_per_extruder}
            extruders_container = {pos: None if not containers else containers[0] for pos, containers in extruders_containers.items()}
            if self._selected_position == self.GLOBAL_STACK_POSITION and global_container:
                quality_changes_metadata = global_container.getMetaData()
            else:
                quality_changes_metadata = extruders_container.get(str(self._selected_position))
            if quality_changes_metadata is not None:  # It can be None if number of extruders are changed during runtime.
                container = container_registry.findContainers(id = quality_changes_metadata["id"])
                if container:
                    quality_containers.insert(0, container[0])

            if global_container:
                settings_keys.update(global_container.getAllKeys())
            for container in extruders_container.values():
                if container:
                    settings_keys.update(container.getAllKeys())

        # We iterate over all definitions instead of settings in a quality/quality_changes group is because in the GUI,
        # the settings are grouped together by categories, and we had to go over all the definitions to figure out
        # which setting belongs in which category.
        current_category = ""
        for definition in definition_container.findDefinitions():
            if definition.type == "category":
                current_category = definition.label
                if self._i18n_catalog:
                    current_category = self._i18n_catalog.i18nc(definition.key + " label", definition.label)
                continue

            profile_value = None
            profile_value_source = ""
            for quality_container in quality_containers:
                new_value = quality_container.getProperty(definition.key, "value")

                if new_value is not None:
                    profile_value_source = quality_container.getMetaDataEntry("type")
                    profile_value = new_value

                # Global tab should use resolve (if there is one)
                if self._selected_position == self.GLOBAL_STACK_POSITION:
                    resolve_value = global_container_stack.getProperty(definition.key, "resolve")
                    if resolve_value is not None and definition.key in settings_keys:
                        profile_value = resolve_value

                if profile_value is not None:
                    break

            if self._selected_position == self.GLOBAL_STACK_POSITION:
                user_value = global_container_stack.userChanges.getProperty(definition.key, "value")
            else:
                extruder_stack = global_container_stack.extruders[str(self._selected_position)]
                user_value = extruder_stack.userChanges.getProperty(definition.key, "value")

            if profile_value is None and user_value is None:
                continue

            label = definition.label
            if self._i18n_catalog:
                label = self._i18n_catalog.i18nc(definition.key + " label", label)

            items.append({
                "key": definition.key,
                "label": label,
                "unit": definition.unit,
                "profile_value": "" if profile_value is None else str(profile_value),  # it is for display only
                "profile_value_source": profile_value_source,
                "user_value": "" if user_value is None else str(user_value),
                "category": current_category
            })

        self.setItems(items)
