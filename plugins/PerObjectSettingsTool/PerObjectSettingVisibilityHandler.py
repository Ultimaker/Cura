# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal

from UM.Application import Application
from UM.Settings.SettingInstance import SettingInstance
from UM.Logger import Logger
import UM.Settings.Models

from cura.Settings.ExtruderManager import ExtruderManager #To get global-inherits-stack setting values from different extruders.
from cura.Settings.SettingOverrideDecorator import SettingOverrideDecorator

##  The per object setting visibility handler ensures that only setting
#   definitions that have a matching instance Container are returned as visible.
class PerObjectSettingVisibilityHandler(UM.Settings.Models.SettingVisibilityHandler):
    def __init__(self, parent = None, *args, **kwargs):
        super().__init__(parent = parent, *args, **kwargs)

        self._selected_object_id = None
        self._node = None
        self._stack = None

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
            if instance.definition.key not in visible:
                settings.removeInstance(instance.definition.key)
                visibility_changed = True

        # Add all instances that are not added, but are in visibility list
        for item in visible:
            if not settings.getInstance(item):
                definition = self._stack.getSettingDefinition(item)
                if definition:
                    new_instance = SettingInstance(definition, settings)
                    stack_nr = -1
                    if definition.global_inherits_stack and self._stack.getProperty("machine_extruder_count", "value") > 1:
                        #Obtain the value from the correct container stack. Only once, upon adding the setting.
                        stack_nr = str(int(round(float(self._stack.getProperty(item, "global_inherits_stack"))))) #Stack to get the setting from. Round it and remove the fractional part.
                    if stack_nr not in ExtruderManager.getInstance().extruderIds and self._stack.getProperty("extruder_nr", "value"): #Property not defined, but we have an extruder number.
                        stack_nr = str(int(round(float(self._stack.getProperty("extruder_nr", "value")))))
                    if stack_nr in ExtruderManager.getInstance().extruderIds: #We have either a global_inherits_stack or an extruder_nr.
                        stack = UM.Settings.ContainerRegistry.getInstance().findContainerStacks(id = ExtruderManager.getInstance().extruderIds[stack_nr])[0]
                    else:
                        stack = UM.Application.getInstance().getGlobalContainerStack()
                    new_instance.setProperty("value", stack.getProperty(item, "value"))
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

