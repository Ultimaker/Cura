# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os
import urllib
from configparser import ConfigParser

from PyQt5.QtCore import pyqtProperty, Qt, pyqtSignal, pyqtSlot, QUrl

from UM.Logger import Logger
from UM.Qt.ListModel import ListModel
from UM.Preferences import Preferences
from UM.Resources import Resources
from UM.MimeTypeDatabase import MimeTypeDatabase, MimeTypeNotFoundError

import cura.CuraApplication


class SettingVisibilityPresetsModel(ListModel):
    IdRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    SettingsRole = Qt.UserRole + 4

    def __init__(self, parent = None):
        super().__init__(parent)
        self.addRoleName(self.IdRole, "id")
        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.SettingsRole, "settings")

        self._populate()

        self._preferences = Preferences.getInstance()
        self._preferences.addPreference("cura/active_setting_visibility_preset", "custom") # Preference to store which preset is currently selected
        self._preferences.addPreference("cura/custom_visible_settings", "") # Preference that stores the "custom" set so it can always be restored (even after a restart)
        self._preferences.preferenceChanged.connect(self._onPreferencesChanged)

        self._active_preset = self._preferences.getValue("cura/active_setting_visibility_preset")
        if self.find("id", self._active_preset) < 0:
            self._active_preset = "custom"

        self.activePresetChanged.emit()


    def _populate(self):
        items = []
        for item in Resources.getAllResourcesOfType(cura.CuraApplication.CuraApplication.ResourceTypes.SettingVisibilityPreset):
            try:
                mime_type = MimeTypeDatabase.getMimeTypeForFile(item)
            except MimeTypeNotFoundError:
                Logger.log("e", "Could not determine mime type of file %s", item)
                continue

            id = urllib.parse.unquote_plus(mime_type.stripExtension(os.path.basename(item)))

            if not os.path.isfile(item):
                continue

            parser = ConfigParser(allow_no_value=True)  # accept options without any value,

            try:
                parser.read([item])

                if not parser.has_option("general", "name") and not parser.has_option("general", "weight"):
                    continue

                settings = []
                for section in parser.sections():
                    if section == 'general':
                        continue

                    settings.append(section)
                    for option in parser[section].keys():
                        settings.append(option)

                items.append({
                    "id": id,
                    "name": parser["general"]["name"],
                    "weight": parser["general"]["weight"],
                    "settings": settings
                })

            except Exception as e:
                Logger.log("e", "Failed to load setting preset %s: %s", file_path, str(e))


        items.sort(key = lambda k: (k["weight"], k["id"]))
        self.setItems(items)

    @pyqtSlot(str)
    def setActivePreset(self, preset_id):
        if preset_id != "custom" and self.find("id", preset_id) == -1:
            Logger.log("w", "Tried to set active preset to unknown id %s", preset_id)
            return

        if preset_id == "custom" and self._active_preset == "custom":
            # Copy current visibility set to custom visibility set preference so it can be restored later
            visibility_string = self._preferences.getValue("general/visible_settings")
            self._preferences.setValue("cura/custom_visible_settings", visibility_string)

        self._preferences.setValue("cura/active_setting_visibility_preset", preset_id)

        self._active_preset = preset_id
        self.activePresetChanged.emit()

    activePresetChanged = pyqtSignal()

    @pyqtProperty(str, notify = activePresetChanged)
    def activePreset(self):
        return self._active_preset

    def _onPreferencesChanged(self, name):
        if name != "general/visible_settings":
            return

        if self._active_preset != "custom":
            return

        # Copy current visibility set to custom visibility set preference so it can be restored later
        visibility_string = self._preferences.getValue("general/visible_settings")
        self._preferences.setValue("cura/custom_visible_settings", visibility_string)


    # Factory function, used by QML
    @staticmethod
    def createSettingVisibilityPresetsModel(engine, js_engine):
        return SettingVisibilityPresetsModel.getInstance()

    ##  Get the singleton instance for this class.
    @classmethod
    def getInstance(cls) -> "SettingVisibilityPresetsModel":
        # Note: Explicit use of class name to prevent issues with inheritance.
        if not SettingVisibilityPresetsModel.__instance:
            SettingVisibilityPresetsModel.__instance = cls()
        return SettingVisibilityPresetsModel.__instance

    __instance = None   # type: "SettingVisibilityPresetsModel"