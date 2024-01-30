#  Copyright (c) 2024 Ultimaker B.V.
#  Cura is released under the terms of the LGPLv3 or higher.

from PyQt6.QtCore import QObject, Qt, pyqtProperty
from UM.FlameProfiler import pyqtSlot
from UM.Application import Application
from UM.Qt.ListModel import ListModel
from UM.Logger import Logger

from .SettingsExportGroup import SettingsExportGroup
from .SettingExport import SettingsExport


class SettingsExportModel(QObject):

    def __init__(self, parent = None):
        super().__init__(parent)
        self._settingsGroups = []
        self._updateSettingsExportGroups()

    @pyqtProperty(list, constant=True)
    def settingsGroups(self):
        return self._settingsGroups

    def _updateSettingsExportGroups(self):
        self._settingsGroups.append(SettingsExportGroup("Global settings",
                                                        SettingsExportGroup.Category.Global,
                                                        [SettingsExport("Generate Support", "Enabled"),
                                                         SettingsExport("Support Type", "Tree")]))
        self._settingsGroups.append(SettingsExportGroup("Extruder settings",
                                                        SettingsExportGroup.Category.Extruder,
                                                        [SettingsExport("Brim Width", "0.7mm")],
                                                        extruder_index=1,
                                                        extruder_color='#ff0000'))
        self._settingsGroups.append(SettingsExportGroup("Extruder settings",
                                                        SettingsExportGroup.Category.Extruder,
                                                        [],
                                                        extruder_index=8,
                                                        extruder_color='#008fff'))
        self._settingsGroups.append(SettingsExportGroup("Model settings",
                                                        SettingsExportGroup.Category.Model,
                                                        [SettingsExport("Brim Width", "20.0 mm"),
                                                         SettingsExport("Z Hop when retracted", "Disabled")],
                                                        'hypercube.stl'))
        self._settingsGroups.append(SettingsExportGroup("Model settings",
                                                        SettingsExportGroup.Category.Model,
                                                        [SettingsExport("Walls Thickness", "3.0 mm"),
                                                         SettingsExport("Enable Ironing", "Enabled")],
                                                        'homer-simpson.stl'))
