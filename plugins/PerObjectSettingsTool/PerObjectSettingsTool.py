# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from UM.Tool import Tool
from UM.Scene.Selection import Selection

from . import PerObjectSettingsModel

class PerObjectSettingsTool(Tool):
    def __init__(self):
        super().__init__()

        self.setExposedProperties("Model", "SelectedIndex")

    def event(self, event):
        return False

    def getModel(self):
        return PerObjectSettingsModel.PerObjectSettingsModel()

    def getSelectedIndex(self):
        selected_object_id = id(Selection.getSelectedObject(0));
        index = self.getModel().find("id", selected_object_id)
        return index