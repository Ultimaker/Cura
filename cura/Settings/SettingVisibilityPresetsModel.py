# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os
import urllib
from configparser import ConfigParser

from PyQt5.QtCore import pyqtProperty, Qt, pyqtSignal, pyqtSlot, QUrl

from UM.Logger import Logger
from UM.Qt.ListModel import ListModel

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

        self._container_ids = []
        self._containers = []

        self._populate()

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