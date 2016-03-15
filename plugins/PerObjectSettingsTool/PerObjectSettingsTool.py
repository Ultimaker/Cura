# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from UM.Tool import Tool
from UM.Scene.Selection import Selection
from UM.Application import Application
from UM.Preferences import Preferences

from . import PerObjectSettingsModel

class PerObjectSettingsTool(Tool):
    def __init__(self):
        super().__init__()
        self._model = None

        self.setExposedProperties("Model", "SelectedIndex")

        Preferences.getInstance().preferenceChanged.connect(self._onPreferenceChanged)
        self._onPreferenceChanged("cura/active_mode")

    def event(self, event):
        return False

    def getModel(self):
        if not self._model:
            self._model = PerObjectSettingsModel.PerObjectSettingsModel()

        #For some reason, casting this model to itself causes the model to properly be cast to a QVariant, even though it ultimately inherits from QVariant.
        #Yeah, we have no idea either...
        return PerObjectSettingsModel.PerObjectSettingsModel(self._model)

    def getSelectedIndex(self):
        try:
            selected_object = Selection.getSelectedObject(0)
            if selected_object.getParent().callDecoration("isGroup"):
                selected_object = selected_object.getParent()
        except:
            selected_object = None
        selected_object_id = id(selected_object)
        index = self.getModel().find("id", selected_object_id)
        return index

    def _onPreferenceChanged(self, preference):
        if preference == "cura/active_mode":
            enabled = Preferences.getInstance().getValue(preference)==1
            Application.getInstance().getController().toolEnabledChanged.emit(self._plugin_id, enabled)