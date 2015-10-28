# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from UM.Tool import Tool

from . import PerObjectSettingsModel

class PerObjectSettingsTool(Tool):
    def __init__(self):
        super().__init__()

        self.setExposedProperties("Model")

    def event(self, event):
        return False

    def getModel(self):
        return PerObjectSettingsModel.PerObjectSettingsModel()
