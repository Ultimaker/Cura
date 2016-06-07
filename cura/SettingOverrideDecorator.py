# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.
from UM.Scene.SceneNodeDecorator import SceneNodeDecorator

from UM.Settings.ContainerStack import ContainerStack
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.ContainerRegistry import ContainerRegistry

from UM.Application import Application
import copy
##  A decorator that adds a container stack to a Node. This stack should be queried for all settings regarding
#   the linked node. The Stack in question will refer to the global stack (so that settings that are not defined by
#   this stack still resolve.
class SettingOverrideDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()
        self._stack = ContainerStack(stack_id = id(self))
        self._stack.setDirty(False)  # This stack does not need to be saved.
        self._instance = InstanceContainer(container_id = "SettingOverrideInstanceContainer")
        self._stack.addContainer(self._instance)

        self._stack.propertyChanged.connect(self._onSettingChanged)

        ContainerRegistry.getInstance().addContainer(self._stack)

        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerStackChanged)
        self._onGlobalContainerStackChanged()

    def __deepcopy__(self, memo):
        ## Create a fresh decorator object
        deep_copy = SettingOverrideDecorator()
        ## Copy the stack
        deep_copy._stack = copy.deepcopy(self._stack, memo)
        ## Ensure that the id is unique.
        deep_copy._stack._id = id(deep_copy)
        return deep_copy

    def _onSettingChanged(self, instance, property):
        if property == "value":  # Only reslice if the value has changed.
            Application.getInstance().getBackend().forceSlice()

    def _onGlobalContainerStackChanged(self):
        ## Ensure that the next stack is always the global stack.
        self._stack.setNextStack(Application.getInstance().getGlobalContainerStack())

    def getStack(self):
        return self._stack