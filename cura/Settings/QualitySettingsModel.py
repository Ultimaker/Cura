# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import collections

from PyQt5.QtCore import pyqtProperty, pyqtSignal, Qt

import UM.Application
import UM.Logger
import UM.Qt
import UM.Settings


class QualitySettingsModel(UM.Qt.ListModel.ListModel):
    KeyRole = Qt.UserRole + 1
    LabelRole = Qt.UserRole + 2
    UnitRole = Qt.UserRole + 3
    ProfileValueRole = Qt.UserRole + 4
    UserValueRole = Qt.UserRole + 5
    CategoryRole = Qt.UserRole + 6

    def __init__(self, parent = None):
        super().__init__(parent = parent)

        self._extruder_id = None
        self._quality = None
        self._material = None

        self.addRoleName(self.KeyRole, "key")
        self.addRoleName(self.LabelRole, "label")
        self.addRoleName(self.UnitRole, "unit")
        self.addRoleName(self.ProfileValueRole, "profile_value")
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

    def setQuality(self, quality):
        if quality != self._quality:
            self._quality = quality
            self._update()
            self.qualityChanged.emit()

    qualityChanged = pyqtSignal()
    @pyqtProperty(str, fset = setQuality, notify = qualityChanged)
    def quality(self):
        return self._quality

    def setMaterial(self, material):
        if material != self._material:
            self._material = material
            self._update()
            self.materialChanged.emit()

    materialChanged = pyqtSignal()
    @pyqtProperty(str, fset = setMaterial, notify = materialChanged)
    def material(self):
        return self._material

    def _update(self):
        if not self._quality:
            return

        self.clear()

        settings = collections.OrderedDict()
        definition_container = UM.Application.getInstance().getGlobalContainerStack().getBottom()

        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(id = self._quality)
        if not containers:
            UM.Logger.log("w", "Could not find a quality container with id %s", self._quality)
            return

        quality_container = None
        quality_changes_container = None

        if containers[0].getMetaDataEntry("type") == "quality":
            quality_container = containers[0]
        else:
            quality_changes_container = containers[0]

            criteria = { "type": "quality", "quality_type": quality_changes_container.getMetaDataEntry("quality"), "definition": quality_changes_container.getDefinition().getId() }

            if self._material:
                criteria["material"] = self._material

            quality_container = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(**criteria)
            if not quality_container:
                UM.Logger.log("w", "Could not find a quality container matching quality changes %s", quality_changes_container.getId())
                return
            quality_container = quality_container[0]

        quality_type = quality_container.getMetaDataEntry("quality_type")

        criteria = { "type": "quality", "quality_type": quality_type }

        if self._material:
            criteria["material"] = self._material

        criteria["extruder"] = self._extruder_id

        containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(**criteria)
        if not containers:
            # Try again, this time without extruder
            criteria.pop("extruder")
            containers = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(**criteria)

            if not containers:
                UM.Logger.log("Could not find any quality containers matching the search criteria %s", criteria)
                return

        if quality_changes_container:
            changes = UM.Settings.ContainerRegistry.getInstance().findInstanceContainers(type = "quality_changes", quality = quality_type, extruder = self._extruder_id)
            if changes:
                containers.extend(changes)

        current_category = ""
        for definition in definition_container.findDefinitions():
            if definition.type == "category":
                current_category = definition.label
                continue

            profile_value = None
            for container in containers:
                new_value = container.getProperty(definition.key, "value")
                if new_value:
                    profile_value = new_value

            user_value = None
            if not self._extruder_id:
                user_value = UM.Application.getInstance().getGlobalContainerStack().getTop().getProperty(definition.key, "value")
            else:
                extruder_stack = UM.Settings.ContainerRegistry.getInstance().findContainerStacks(id = self._extruder_id)
                if extruder_stack:
                    user_value = extruder_stack[0].getTop().getProperty(definition.key, "value")

            if not profile_value and not user_value:
                continue

            self.appendItem({
                "key": definition.key,
                "label": definition.label,
                "unit": definition.unit,
                "profile_value": "" if profile_value is None else str(profile_value),  # it is for display only
                "user_value": "" if user_value is None else str(user_value),
                "category": current_category
            })
