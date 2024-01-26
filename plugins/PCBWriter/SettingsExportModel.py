#  Copyright (c) 2024 Ultimaker B.V.
#  Cura is released under the terms of the LGPLv3 or higher.

from PyQt6.QtCore import QObject, Qt, pyqtProperty
from UM.FlameProfiler import pyqtSlot
from UM.Application import Application
from UM.Qt.ListModel import ListModel
from UM.Logger import Logger

from .SettingsExportGroup import SettingsExportGroup


class SettingsExportModel(QObject):

    def __init__(self, parent = None):
        super().__init__(parent)
        self._settingsGroups = []
        self._updateSettingsExportGroups()

    @pyqtProperty(list, constant=True)
    def settingsGroups(self):
        return self._settingsGroups

    def _updateSettingsExportGroups(self):
        self._settingsGroups.append(SettingsExportGroup("Global settings", SettingsExportGroup.Category.Global))
        self._settingsGroups.append(SettingsExportGroup("Extruder settings", SettingsExportGroup.Category.Extruder, extruder_index=1, extruder_color='#ff0000'))
        self._settingsGroups.append(SettingsExportGroup("Extruder settings", SettingsExportGroup.Category.Extruder, extruder_index=8, extruder_color='#008fff'))
        self._settingsGroups.append(SettingsExportGroup("Model settings",
                                                        SettingsExportGroup.Category.Model, 'hypercube.stl'))
        self._settingsGroups.append(SettingsExportGroup("Model settings",
                                                        SettingsExportGroup.Category.Model, 'homer-simpson.stl'))
