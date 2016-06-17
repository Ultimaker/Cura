# Copyright (c) 2016 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from UM.Tool import Tool
from UM.Scene.Selection import Selection
from UM.Application import Application
from UM.Preferences import Preferences
from cura.SettingOverrideDecorator import SettingOverrideDecorator

##  This tool allows the user to add & change settings per node in the scene.
#   The settings per object are kept in a ContainerStack, which is linked to a node by decorator.
class PerObjectSettingsTool(Tool):
    def __init__(self):
        super().__init__()
        self._model = None

        self.setExposedProperties("SelectedObjectId", "ContainerID", "SelectedActiveExtruder")

        Preferences.getInstance().preferenceChanged.connect(self._onPreferenceChanged)
        Selection.selectionChanged.connect(self.propertyChanged)
        self._onPreferenceChanged("cura/active_mode")

    def event(self, event):
        return False

    def getSelectedObjectId(self):
        selected_object = Selection.getSelectedObject(0)
        selected_object_id = id(selected_object)
        return selected_object_id

    def getContainerID(self):
        selected_object = Selection.getSelectedObject(0)
        try:
            return selected_object.callDecoration("getStack").getId()
        except AttributeError:
            return ""

    ##  Gets the active extruder of the currently selected object.
    #
    #   \return The active extruder of the currently selected object.
    def getSelectedActiveExtruder(self):
        selected_object = Selection.getSelectedObject(0)
        return selected_object.callDecoration("getActiveExtruder")

    ##  Changes the active extruder of the currently selected object.
    #
    #   \param extruder_stack_id The ID of the extruder to print the currently
    #   selected object with.
    def setSelectedActiveExtruder(self, extruder_stack_id):
        selected_object = Selection.getSelectedObject(0)
        stack = selected_object.callDecoration("getStack") #Don't try to get the active extruder since it may be None anyway.
        if not stack:
            selected_object.addDecorator(SettingOverrideDecorator())
        selected_object.callDecoration("setActiveExtruder", extruder_stack_id)

    def _onPreferenceChanged(self, preference):
        if preference == "cura/active_mode":
            enabled = Preferences.getInstance().getValue(preference)==1
            Application.getInstance().getController().toolEnabledChanged.emit(self._plugin_id, enabled)