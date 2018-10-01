# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional
import os
import urllib.parse
from configparser import ConfigParser

from PyQt5.QtCore import pyqtProperty, Qt, pyqtSignal, pyqtSlot

from UM.Application import Application
from UM.Logger import Logger
from UM.Qt.ListModel import ListModel
from UM.Resources import Resources
from UM.MimeTypeDatabase import MimeTypeDatabase, MimeTypeNotFoundError

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


class SettingVisibilityPresetsModel(ListModel):
    IdRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    SettingsRole = Qt.UserRole + 3

    def __init__(self, parent = None):
        super().__init__(parent)
        self.addRoleName(self.IdRole, "id")
        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.SettingsRole, "settings")

        self._populate()
        basic_item = self.items[1]
        basic_visibile_settings = ";".join(basic_item["settings"])

        self._preferences = Application.getInstance().getPreferences()
        # Preference to store which preset is currently selected
        self._preferences.addPreference("cura/active_setting_visibility_preset", "basic")
        # Preference that stores the "custom" set so it can always be restored (even after a restart)
        self._preferences.addPreference("cura/custom_visible_settings", basic_visibile_settings)
        self._preferences.preferenceChanged.connect(self._onPreferencesChanged)

        self._active_preset_item = self._getItem(self._preferences.getValue("cura/active_setting_visibility_preset"))
        # Initialize visible settings if it is not done yet
        visible_settings = self._preferences.getValue("general/visible_settings")
        if not visible_settings:
            self._preferences.setValue("general/visible_settings", ";".join(self._active_preset_item["settings"]))
        else:
            self._onPreferencesChanged("general/visible_settings")

        self.activePresetChanged.emit()

    def _getItem(self, item_id: str) -> Optional[dict]:
        result = None
        for item in self.items:
            if item["id"] == item_id:
                result = item
                break
        return result

    def _populate(self) -> None:
        from cura.CuraApplication import CuraApplication
        items = []
        for file_path in Resources.getAllResourcesOfType(CuraApplication.ResourceTypes.SettingVisibilityPreset):
            try:
                mime_type = MimeTypeDatabase.getMimeTypeForFile(file_path)
            except MimeTypeNotFoundError:
                Logger.log("e", "Could not determine mime type of file %s", file_path)
                continue

            item_id = urllib.parse.unquote_plus(mime_type.stripExtension(os.path.basename(file_path)))
            if not os.path.isfile(file_path):
                Logger.log("e", "[%s] is not a file", file_path)
                continue

            parser = ConfigParser(allow_no_value = True)  # accept options without any value,
            try:
                parser.read([file_path])
                if not parser.has_option("general", "name") or not parser.has_option("general", "weight"):
                    continue

                settings = []
                for section in parser.sections():
                    if section == 'general':
                        continue

                    settings.append(section)
                    for option in parser[section].keys():
                        settings.append(option)

                items.append({
                    "id": item_id,
                    "name": catalog.i18nc("@action:inmenu", parser["general"]["name"]),
                    "weight": parser["general"]["weight"],
                    "settings": settings,
                })

            except Exception:
                Logger.logException("e", "Failed to load setting preset %s", file_path)

        items.sort(key = lambda k: (int(k["weight"]), k["id"]))
        # Put "custom" at the top
        items.insert(0, {"id": "custom",
                         "name": "Custom selection",
                         "weight": -100,
                         "settings": []})

        self.setItems(items)

    @pyqtSlot(str)
    def setActivePreset(self, preset_id: str):
        if preset_id == self._active_preset_item["id"]:
            Logger.log("d", "Same setting visibility preset [%s] selected, do nothing.", preset_id)
            return

        preset_item = None
        for item in self.items:
            if item["id"] == preset_id:
                preset_item = item
                break
        if preset_item is None:
            Logger.log("w", "Tried to set active preset to unknown id [%s]", preset_id)
            return

        need_to_save_to_custom = self._active_preset_item["id"] == "custom" and preset_id != "custom"
        if need_to_save_to_custom:
            # Save the current visibility settings to custom
            current_visibility_string = self._preferences.getValue("general/visible_settings")
            if current_visibility_string:
                self._preferences.setValue("cura/custom_visible_settings", current_visibility_string)

        new_visibility_string = ";".join(preset_item["settings"])
        if preset_id == "custom":
            # Get settings from the stored custom data
            new_visibility_string = self._preferences.getValue("cura/custom_visible_settings")
            if new_visibility_string is None:
                new_visibility_string = self._preferences.getValue("general/visible_settings")
        self._preferences.setValue("general/visible_settings", new_visibility_string)

        self._preferences.setValue("cura/active_setting_visibility_preset", preset_id)
        self._active_preset_item = preset_item
        self.activePresetChanged.emit()

    activePresetChanged = pyqtSignal()

    @pyqtProperty(str, notify = activePresetChanged)
    def activePreset(self) -> str:
        return self._active_preset_item["id"]

    def _onPreferencesChanged(self, name: str) -> None:
        if name != "general/visible_settings":
            return

        # Find the preset that matches with the current visible settings setup
        visibility_string = self._preferences.getValue("general/visible_settings")
        if not visibility_string:
            return

        visibility_set = set(visibility_string.split(";"))
        matching_preset_item = None
        for item in self.items:
            if item["id"] == "custom":
                continue
            if set(item["settings"]) == visibility_set:
                matching_preset_item = item
                break

        item_to_set = self._active_preset_item
        if matching_preset_item is None:
            # The new visibility setup is "custom" should be custom
            if self._active_preset_item["id"] == "custom":
                # We are already in custom, just save the settings
                self._preferences.setValue("cura/custom_visible_settings", visibility_string)
            else:
                item_to_set = self.items[0]  # 0 is custom
        else:
            item_to_set = matching_preset_item

        if self._active_preset_item is None or self._active_preset_item["id"] != item_to_set["id"]:
            self._active_preset_item = item_to_set
            self._preferences.setValue("cura/active_setting_visibility_preset", self._active_preset_item["id"])
            self.activePresetChanged.emit()
