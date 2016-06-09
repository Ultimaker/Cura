# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import pyqtSignal
import copy

from UM.Scene.SceneNodeDecorator import SceneNodeDecorator

from UM.Settings.ContainerStack import ContainerStack
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.ContainerRegistry import ContainerRegistry

from UM.Application import Application

##  A decorator that adds a container stack to a Node. This stack should be queried for all settings regarding
#   the linked node. The Stack in question will refer to the global stack (so that settings that are not defined by
#   this stack still resolve.
class SettingOverrideDecorator(SceneNodeDecorator):
    ##  Event indicating that the user selected a different extruder.
    activeExtruderChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._stack = ContainerStack(stack_id = id(self))
        self._stack.setDirty(False)  # This stack does not need to be saved.
        self._instance = InstanceContainer(container_id = "SettingOverrideInstanceContainer")
        self._stack.addContainer(self._instance)
        self._extruder_stack = None #Stack upon which our stack is based.

        self._stack.propertyChanged.connect(self._onSettingChanged)

        ContainerRegistry.getInstance().addContainer(self._stack)

        Application.getInstance().globalContainerStackChanged.connect(self._updateNextStack)
        self.activeExtruderChanged.connect(self._updateNextStack)
        self._updateNextStack()

    def __deepcopy__(self, memo):
        ## Create a fresh decorator object
        deep_copy = SettingOverrideDecorator()
        ## Copy the instance
        deep_copy._instance = copy.deepcopy(self._instance, memo)
        ## Set the copied instance as the first (and only) instance container of the stack.
        deep_copy._stack.replaceContainer(0, deep_copy._instance)
        return deep_copy

    ##  Gets the currently active extruder to print this object with.
    #
    #   \return An extruder's container stack.
    def getActiveExtruder(self):
        return self._extruder_stack

    def _onSettingChanged(self, instance, property):
        if property == "value":  # Only reslice if the value has changed.
            Application.getInstance().getBackend().forceSlice()

    ##  Makes sure that the stack upon which the container stack is placed is
    #   kept up to date.
    def _updateNextStack(self):
        if self._extruder_stack:
            self._stack.setNextStack(ContainerRegistry.getInstance().findContainerStack(id = self._extruder_stack))
        else:
            self._stack.setNextStack(Application.getInstance().getGlobalContainerStack())

    ##  Changes the extruder with which to print this node.
    #
    #   \param extruder_stack_id The new extruder stack to print with.
    def setActiveExtruder(self, extruder_stack_id):
        self._extruder_stack = extruder_stack_id
        self.activeExtruderChanged.emit()

    def getStack(self):
        return self._stack