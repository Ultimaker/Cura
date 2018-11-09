# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, List

from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject

from UM.Logger import Logger
from UM.Resources import Resources

from UM.i18n import i18nCatalog
from cura.Settings.SettingVisibilityPreset import SettingVisibilityPreset

catalog = i18nCatalog("cura")


class SettingVisibilityPresetsModel(QObject):
    onItemsChanged = pyqtSignal()
    activePresetChanged = pyqtSignal()

    def __init__(self, preferences, parent = None):
        super().__init__(parent)

        self._items = []  # type: List[SettingVisibilityPreset]
        self._populate()

        basic_item = self.getVisibilityPresetById("basic")
        basic_visibile_settings = ";".join(basic_item.settings)

        self._preferences = preferences

        # Preference to store which preset is currently selected
        self._preferences.addPreference("cura/active_setting_visibility_preset", "basic")

        # Preference that stores the "custom" set so it can always be restored (even after a restart)
        self._preferences.addPreference("cura/custom_visible_settings", basic_visibile_settings)
        self._preferences.preferenceChanged.connect(self._onPreferencesChanged)

        self._active_preset_item = self.getVisibilityPresetById(self._preferences.getValue("cura/active_setting_visibility_preset"))

        # Initialize visible settings if it is not done yet
        visible_settings = self._preferences.getValue("general/visible_settings")

        if not visible_settings:
            self._preferences.setValue("general/visible_settings", ";".join(self._active_preset_item.settings))
        else:
            self._onPreferencesChanged("general/visible_settings")

        self.activePresetChanged.emit()

    def getVisibilityPresetById(self, item_id: str) -> Optional[SettingVisibilityPreset]:
        result = None
        for item in self._items:
            if item.presetId == item_id:
                result = item
                break
        return result

    def _populate(self) -> None:
        from cura.CuraApplication import CuraApplication
        items = []  # type: List[SettingVisibilityPreset]

        custom_preset = SettingVisibilityPreset(preset_id="custom", name ="Custom selection", weight = -100)
        items.append(custom_preset)
        for file_path in Resources.getAllResourcesOfType(CuraApplication.ResourceTypes.SettingVisibilityPreset):
            setting_visibility_preset = SettingVisibilityPreset()
            try:
                setting_visibility_preset.loadFromFile(file_path)
            except Exception:
                Logger.logException("e", "Failed to load setting preset %s", file_path)

            items.append(setting_visibility_preset)

        # Sort them on weight (and if that fails, use ID)
        items.sort(key = lambda k: (int(k.weight), k.presetId))

        self.setItems(items)

    @pyqtProperty("QVariantList", notify = onItemsChanged)
    def items(self):
        return self._items

    def setItems(self, items: List[SettingVisibilityPreset]) -> None:
        if self._items != items:
            self._items = items
            self.onItemsChanged.emit()

    @pyqtSlot(str)
    def setActivePreset(self, preset_id: str) -> None:
        if preset_id == self._active_preset_item.presetId:
            Logger.log("d", "Same setting visibility preset [%s] selected, do nothing.", preset_id)
            return

        preset_item = self.getVisibilityPresetById(preset_id)
        if preset_item is None:
            Logger.log("w", "Tried to set active preset to unknown id [%s]", preset_id)
            return

        need_to_save_to_custom = self._active_preset_item.presetId == "custom" and preset_id != "custom"
        if need_to_save_to_custom:
            # Save the current visibility settings to custom
            current_visibility_string = self._preferences.getValue("general/visible_settings")
            if current_visibility_string:
                self._preferences.setValue("cura/custom_visible_settings", current_visibility_string)

        new_visibility_string = ";".join(preset_item.settings)
        if preset_id == "custom":
            # Get settings from the stored custom data
            new_visibility_string = self._preferences.getValue("cura/custom_visible_settings")
            if new_visibility_string is None:
                new_visibility_string = self._preferences.getValue("general/visible_settings")
        self._preferences.setValue("general/visible_settings", new_visibility_string)

        self._preferences.setValue("cura/active_setting_visibility_preset", preset_id)
        self._active_preset_item = preset_item
        self.activePresetChanged.emit()

    @pyqtProperty(str, notify = activePresetChanged)
    def activePreset(self) -> str:
        return self._active_preset_item.presetId

    def _onPreferencesChanged(self, name: str) -> None:
        if name != "general/visible_settings":
            return

        # Find the preset that matches with the current visible settings setup
        visibility_string = self._preferences.getValue("general/visible_settings")
        if not visibility_string:
            return

        visibility_set = set(visibility_string.split(";"))
        matching_preset_item = None
        for item in self._items:
            if item.presetId == "custom":
                continue
            if set(item.settings) == visibility_set:
                matching_preset_item = item
                break

        item_to_set = self._active_preset_item
        if matching_preset_item is None:
            # The new visibility setup is "custom" should be custom
            if self._active_preset_item is None or self._active_preset_item.presetId == "custom":
                # We are already in custom, just save the settings
                self._preferences.setValue("cura/custom_visible_settings", visibility_string)
            else:
                # We need to move to custom preset.
                item_to_set = self.getVisibilityPresetById("custom")
        else:
            item_to_set = matching_preset_item

        if self._active_preset_item is None or self._active_preset_item.presetId != item_to_set.presetId:
            self._active_preset_item = item_to_set
            self._preferences.setValue("cura/active_setting_visibility_preset", self._active_preset_item.presetId)
            self.activePresetChanged.emit()
