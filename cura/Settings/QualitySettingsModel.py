# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import collections

from PyQt5.QtCore import pyqtProperty, pyqtSignal, Qt

from UM.Logger import Logger
import UM.Qt
from UM.Application import Application
from UM.Settings.ContainerRegistry import ContainerRegistry
import os

from UM.i18n import i18nCatalog


class QualitySettingsModel(UM.Qt.ListModel.ListModel):
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

        self._extruder_id = None
        self._extruder_definition_id = None
        self._quality_id = None
        self._material_id = None
        self._i18n_catalog = None

        self.addRoleName(self.KeyRole, "key")
        self.addRoleName(self.LabelRole, "label")
        self.addRoleName(self.UnitRole, "unit")
        self.addRoleName(self.ProfileValueRole, "profile_value")
        self.addRoleName(self.ProfileValueSourceRole, "profile_value_source")
        self.addRoleName(self.UserValueRole, "user_value")
        self.addRoleName(self.CategoryRole, "category")

    def setExtruderId(self, extruder_id):
        if extruder_id != self._extruder_id:
            self._extruder_id = extruder_id
            self._update()
            self.extruderIdChanged.emit()

    extruderIdChanged = pyqtSignal()
    @pyqtProperty(str, fset = setExtruderId, notify = extruderIdChanged)
    def extruderId(self):
        return self._extruder_id

    def setExtruderDefinition(self, extruder_definition):
        if extruder_definition != self._extruder_definition_id:
            self._extruder_definition_id = extruder_definition
            self._update()
            self.extruderDefinitionChanged.emit()

    extruderDefinitionChanged = pyqtSignal()
    @pyqtProperty(str, fset = setExtruderDefinition, notify = extruderDefinitionChanged)
    def extruderDefinition(self):
        return self._extruder_definition_id

    def setQuality(self, quality):
        if quality != self._quality_id:
            self._quality_id = quality
            self._update()
            self.qualityChanged.emit()

    qualityChanged = pyqtSignal()
    @pyqtProperty(str, fset = setQuality, notify = qualityChanged)
    def quality(self):
        return self._quality_id

    def setMaterial(self, material):
        if material != self._material_id:
            self._material_id = material
            self._update()
            self.materialChanged.emit()

    materialChanged = pyqtSignal()
    @pyqtProperty(str, fset = setMaterial, notify = materialChanged)
    def material(self):
        return self._material_id

    def _update(self):
        if not self._quality_id:
            return

        items = []

        settings = collections.OrderedDict()
        definition_container = Application.getInstance().getGlobalContainerStack().getBottom()

        containers = self._container_registry.findInstanceContainers(id = self._quality_id)
        if not containers:
            Logger.log("w", "Could not find a quality container with id %s", self._quality_id)
            return

        quality_container = None
        quality_changes_container = None

        if containers[0].getMetaDataEntry("type") == "quality":
            quality_container = containers[0]
        else:
            quality_changes_container = containers[0]

            criteria = {
                "type": "quality",
                "quality_type": quality_changes_container.getMetaDataEntry("quality_type"),
                "definition": quality_changes_container.getDefinition().getId()
            }

            quality_container = self._container_registry.findInstanceContainers(**criteria)
            if not quality_container:
                Logger.log("w", "Could not find a quality container matching quality changes %s", quality_changes_container.getId())
                return
            quality_container = quality_container[0]

        quality_type = quality_container.getMetaDataEntry("quality_type")
        definition_id = Application.getInstance().getMachineManager().getQualityDefinitionId(quality_container.getDefinition())
        definition = quality_container.getDefinition()

        # Check if the definition container has a translation file.
        definition_suffix = ContainerRegistry.getMimeTypeForContainer(type(definition)).preferredSuffix
        catalog = i18nCatalog(os.path.basename(definition_id + "." + definition_suffix))
        if catalog.hasTranslationLoaded():
            self._i18n_catalog = catalog

        for file_name in quality_container.getDefinition().getInheritedFiles():
            catalog = i18nCatalog(os.path.basename(file_name))
            if catalog.hasTranslationLoaded():
                self._i18n_catalog = catalog

        criteria = {"type": "quality", "quality_type": quality_type, "definition": definition_id}

        if self._material_id and self._material_id != "empty_material":
            criteria["material"] = self._material_id

        criteria["extruder"] = self._extruder_id

        containers = self._container_registry.findInstanceContainers(**criteria)
        if not containers:
            # Try again, this time without extruder
            new_criteria = criteria.copy()
            new_criteria.pop("extruder")
            containers = self._container_registry.findInstanceContainers(**new_criteria)

        if not containers and "material" in criteria:
            # Try again, this time without material
            criteria.pop("material", None)
            containers = self._container_registry.findInstanceContainers(**criteria)

        if not containers:
            # Try again, this time without material or extruder
            criteria.pop("extruder") # "material" has already been popped
            containers = self._container_registry.findInstanceContainers(**criteria)

        if not containers:
            Logger.log("w", "Could not find any quality containers matching the search criteria %s" % str(criteria))
            return

        if quality_changes_container:
            criteria = {"type": "quality_changes", "quality_type": quality_type, "definition": definition_id, "name": quality_changes_container.getName()}
            if self._extruder_definition_id != "":
                extruder_definitions = self._container_registry.findDefinitionContainers(id = self._extruder_definition_id)
                if extruder_definitions:
                    criteria["extruder"] = Application.getInstance().getMachineManager().getQualityDefinitionId(extruder_definitions[0])
                    criteria["name"] = quality_changes_container.getName()
            else:
                criteria["extruder"] = None

            changes = self._container_registry.findInstanceContainers(**criteria)
            if changes:
                containers.extend(changes)

        global_container_stack = Application.getInstance().getGlobalContainerStack()
        is_multi_extrusion = global_container_stack.getProperty("machine_extruder_count", "value") > 1

        current_category = ""
        for definition in definition_container.findDefinitions():
            if definition.type == "category":
                current_category = definition.label
                if self._i18n_catalog:
                    current_category = self._i18n_catalog.i18nc(definition.key + " label", definition.label)
                continue

            profile_value = None
            profile_value_source = ""
            for container in containers:
                new_value = container.getProperty(definition.key, "value")

                if new_value is not None:
                    profile_value_source = container.getMetaDataEntry("type")
                    profile_value = new_value

                # Global tab should use resolve (if there is one)
                if not self._extruder_id:
                    resolve_value = global_container_stack.getProperty(definition.key, "resolve")
                    if resolve_value is not None and profile_value is not None and profile_value_source != "quality_changes":
                        profile_value = resolve_value

            user_value = None
            if not self._extruder_id:
                user_value = global_container_stack.getTop().getProperty(definition.key, "value")
            else:
                extruder_stack = self._container_registry.findContainerStacks(id = self._extruder_id)
                if extruder_stack:
                    user_value = extruder_stack[0].getTop().getProperty(definition.key, "value")

            if profile_value is None and user_value is None:
                continue

            if is_multi_extrusion:
                settable_per_extruder = global_container_stack.getProperty(definition.key, "settable_per_extruder")
                # If a setting is not settable per extruder (global) and we're looking at an extruder tab, don't show this value.
                if self._extruder_id != "" and not settable_per_extruder:
                    continue

                # If a setting is settable per extruder (not global) and we're looking at global tab, don't show this value.
                if self._extruder_id == "" and settable_per_extruder:
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
