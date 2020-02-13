# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty
from UM.FlameProfiler import pyqtSlot

from UM.Application import Application
from UM.PluginRegistry import PluginRegistry
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.SettingInstance import SettingInstance
from UM.Logger import Logger
import UM.Settings.Models.SettingVisibilityHandler

from cura.Settings.ExtruderManager import ExtruderManager #To get global-inherits-stack setting values from different extruders.
from cura.Settings.SettingOverrideDecorator import SettingOverrideDecorator


##  The per object setting visibility handler ensures that only setting
#   definitions that have a matching instance Container are returned as visible.
class PerObjectSettingVisibilityHandler(UM.Settings.Models.SettingVisibilityHandler.SettingVisibilityHandler):
    def __init__(self, parent = None, *args, **kwargs):
        super().__init__(parent = parent, *args, **kwargs)

        self._selected_object_id = None
        self._node = None
        self._stack = None

        PluginRegistry.getInstance().getPluginObject("PerObjectSettingsTool").visibility_handler = self

        # this is a set of settings that will be skipped if the user chooses to reset.
        self._skip_reset_setting_set = set()

    def setSelectedObjectId(self, id):
        if id != self._selected_object_id:
            self._selected_object_id = id

            self._node = Application.getInstance().getController().getScene().findObject(self._selected_object_id)
            if self._node:
                self._stack = self._node.callDecoration("getStack")

            self.visibilityChanged.emit()

    @pyqtProperty("quint64", fset = setSelectedObjectId)
    def selectedObjectId(self):
        return self._selected_object_id

    @pyqtSlot(str)
    def addSkipResetSetting(self, setting_name):
        self._skip_reset_setting_set.add(setting_name)

    def setVisible(self, visible):
        if not self._node:
            return

        if not self._stack:
            self._node.addDecorator(SettingOverrideDecorator())
            self._stack = self._node.callDecoration("getStack")

        settings = self._stack.getTop()
        all_instances = settings.findInstances()
        visibility_changed = False  # Flag to check if at the end the signal needs to be emitted

        # Remove all instances that are not in visibility list
        for instance in all_instances:
            # exceptionally skip setting
            if instance.definition.key in self._skip_reset_setting_set:
                continue
            if instance.definition.key not in visible:
                settings.removeInstance(instance.definition.key)
                visibility_changed = True

        # Add all instances that are not added, but are in visibility list
        for item in visible:
            if not settings.getInstance(item): # Setting was not added already.
                definition = self._stack.getSettingDefinition(item)
                if definition:
                    new_instance = SettingInstance(definition, settings)
                    stack_nr = -1
                    stack = None
                    # Check from what stack we should copy the raw property of the setting from.
                    if self._stack.getProperty("machine_extruder_count", "value") > 1:
                        if definition.limit_to_extruder != "-1":
                            # A limit to extruder function was set and it's a multi extrusion machine. Check what stack we do need to use.
                            stack_nr = str(int(round(float(self._stack.getProperty(item, "limit_to_extruder")))))

                        # Check if the found stack_number is in the extruder list of extruders.
                        if stack_nr not in ExtruderManager.getInstance().extruderIds and self._stack.getProperty("extruder_nr", "value") is not None:
                            stack_nr = -1

                        # Use the found stack number to get the right stack to copy the value from.
                        if stack_nr in ExtruderManager.getInstance().extruderIds:
                            stack = ContainerRegistry.getInstance().findContainerStacks(id = ExtruderManager.getInstance().extruderIds[stack_nr])[0]
                    else:
                        stack = self._stack

                    # Use the raw property to set the value (so the inheritance doesn't break)
                    if stack is not None:
                        new_instance.setProperty("value", stack.getRawProperty(item, "value"))
                    else:
                        new_instance.setProperty("value", None)
                    new_instance.resetState()  # Ensure that the state is not seen as a user state.
                    settings.addInstance(new_instance)
                    visibility_changed = True
                else:
                    Logger.log("w", "Unable to add instance (%s) to per-object visibility because we couldn't find the matching definition", item)

        if visibility_changed:
            self.visibilityChanged.emit()

    def getVisible(self):
        visible_settings = set()
        if not self._node:
            return visible_settings

        if not self._stack:
            return visible_settings

        settings = self._stack.getTop()
        if not settings:
            return visible_settings

        visible_settings = set(map(lambda i: i.definition.key, settings.findInstances()))
        return visible_settings

