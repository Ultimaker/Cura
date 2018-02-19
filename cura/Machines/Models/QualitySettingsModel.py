# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty, pyqtSignal, Qt

from UM.Application import Application
from UM.Qt.ListModel import ListModel
from UM.Settings.ContainerRegistry import ContainerRegistry


class QualitySettingsModel(ListModel):
    KeyRole = Qt.UserRole + 1
    LabelRole = Qt.UserRole + 2
    UnitRole = Qt.UserRole + 3
    ProfileValueRole = Qt.UserRole + 4
    ProfileValueSourceRole = Qt.UserRole + 5
    UserValueRole = Qt.UserRole + 6
    CategoryRole = Qt.UserRole + 7

    def __init__(self, parent = None):
        super().__init__(parent = parent)

        self._container_registry = ContainerRegistry.getInstance()
        self._application = Application.getInstance()
        self._quality_manager = self._application._quality_manager

        self._extruder_position = ""
        self._quality = None
        self._i18n_catalog = None

        self.addRoleName(self.KeyRole, "key")
        self.addRoleName(self.LabelRole, "label")
        self.addRoleName(self.UnitRole, "unit")
        self.addRoleName(self.ProfileValueRole, "profile_value")
        self.addRoleName(self.ProfileValueSourceRole, "profile_value_source")
        self.addRoleName(self.UserValueRole, "user_value")
        self.addRoleName(self.CategoryRole, "category")

        self._empty_quality = self._container_registry.findInstanceContainers(id = "empty_quality")[0]

        self._update()
        self._quality_manager.qualitiesUpdated.connect(self._update)

    extruderPositionChanged = pyqtSignal()
    qualityChanged = pyqtSignal()

    def setExtruderPosition(self, extruder_position):
        if extruder_position != self._extruder_position:
            self._extruder_position = extruder_position
            self._update()
            self.extruderPositionChanged.emit()

    @pyqtProperty(str, fset = setExtruderPosition, notify = extruderPositionChanged)
    def extruderPosition(self):
        return self._extruder_position

    def setQuality(self, quality):
        if quality != self._quality:
            self._quality = quality
            self._update()
            self.qualityChanged.emit()

    @pyqtProperty("QVariantMap", fset = setQuality, notify = qualityChanged)
    def quality(self):
        return self._quality

    def _update(self):
        if self._quality is None:
            self.setItems([])
            return

        items = []

        global_container_stack = Application.getInstance().getGlobalContainerStack()
        definition_container = global_container_stack.definition

        quality_group = self._quality["quality_group"]
        quality_changes_group = self._quality["quality_changes_group"]

        if self._extruder_position == "":
            quality_node = quality_group.node_for_global
        else:
            quality_node = quality_group.nodes_for_extruders.get(self._extruder_position)
        settings_keys = quality_group.getAllKeys()
        quality_containers = [quality_node.getContainer()]

        if quality_changes_group is not None:
            if self._extruder_position == "":
                quality_changes_node = quality_changes_group.node_for_global
            else:
                quality_changes_node = quality_changes_group.nodes_for_extruders.get(self._extruder_position)
            if quality_changes_node is not None:  # it can be None if number of extruders are changed during runtime
                quality_containers.insert(0, quality_changes_node.getContainer())
            settings_keys.update(quality_changes_group.getAllKeys())

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
                if self._extruder_position == "":
                    resolve_value = global_container_stack.getProperty(definition.key, "resolve")
                    if resolve_value is not None and definition.key in settings_keys:
                        profile_value = resolve_value

                if profile_value is not None:
                    break

            if not self._extruder_position:
                user_value = global_container_stack.userChanges.getProperty(definition.key, "value")
            else:
                extruder_stack = global_container_stack.extruders[self._extruder_position]
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
