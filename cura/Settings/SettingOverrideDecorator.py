# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import copy

from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
from UM.Signal import Signal, signalemitter
from UM.Settings.ContainerStack import ContainerStack
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.ContainerRegistry import ContainerRegistry
import UM.Logger

import cura.Settings

from UM.Application import Application

##  A decorator that adds a container stack to a Node. This stack should be queried for all settings regarding
#   the linked node. The Stack in question will refer to the global stack (so that settings that are not defined by
#   this stack still resolve.
@signalemitter
class SettingOverrideDecorator(SceneNodeDecorator):
    ##  Event indicating that the user selected a different extruder.
    activeExtruderChanged = Signal()

    def __init__(self):
        super().__init__()
        self._stack = ContainerStack(stack_id = id(self))
        self._stack.setDirty(False)  # This stack does not need to be saved.
        self._instance = InstanceContainer(container_id = "SettingOverrideInstanceContainer")
        self._stack.addContainer(self._instance)

        if cura.Settings.ExtruderManager.getInstance().extruderCount > 1:
            self._extruder_stack = cura.Settings.ExtruderManager.getInstance().getExtruderStack(0).getId()
        else:
            self._extruder_stack = None

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

        # Properly set the right extruder on the copy
        deep_copy.setActiveExtruder(self._extruder_stack)

        ## Set the copied instance as the first (and only) instance container of the stack.
        deep_copy._stack.replaceContainer(0, deep_copy._instance)
        return deep_copy

    ##  Gets the currently active extruder to print this object with.
    #
    #   \return An extruder's container stack.
    def getActiveExtruder(self):
        return self._extruder_stack

    def _onSettingChanged(self, instance, property_name): # Reminder: 'property' is a built-in function
        if property_name == "value":  # Only reslice if the value has changed.
            Application.getInstance().getBackend().forceSlice()

    ##  Makes sure that the stack upon which the container stack is placed is
    #   kept up to date.
    def _updateNextStack(self):
        if self._extruder_stack:
            extruder_stack = ContainerRegistry.getInstance().findContainerStacks(id = self._extruder_stack)
            if extruder_stack:
                if self._stack.getNextStack():
                    old_extruder_stack_id = self._stack.getNextStack().getId()
                else:
                    old_extruder_stack_id = ""

                self._stack.setNextStack(extruder_stack[0])
                if self._stack.getNextStack().getId() != old_extruder_stack_id: #Only reslice if the extruder changed.
                    Application.getInstance().getBackend().forceSlice()
            else:
                UM.Logger.log("e", "Extruder stack %s below per-object settings does not exist.", self._extruder_stack)
        else:
            self._stack.setNextStack(Application.getInstance().getGlobalContainerStack())

    ##  Changes the extruder with which to print this node.
    #
    #   \param extruder_stack_id The new extruder stack to print with.
    def setActiveExtruder(self, extruder_stack_id):
        self._extruder_stack = extruder_stack_id
        self._updateNextStack()
        self.activeExtruderChanged.emit()

    def getStack(self):
        return self._stack
