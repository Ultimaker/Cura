# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.
from UM.Scene.SceneNodeDecorator import SceneNodeDecorator

from UM.Settings.ContainerStack import ContainerStack
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.ContainerRegistry import ContainerRegistry

from UM.Application import Application

##  A decorator that adds a container stack to a Node. This stack should be queried for all settings regarding
#   the linked node. The Stack in question will refer to the global stack (so that settings that are not defined by
#   this stack still resolve.
class SettingOverrideDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()
        self._stack = ContainerStack(id = "SettingOverrideStack")
        self._instance = InstanceContainer(id = "SettingOverrideInstanceContainer")
        self._stack.addContainer(self._instance)

        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalContainerStackChanged)
        self._onGlobalContainerStackChanged()

    def _onGlobalContainerStackChanged(self):
        ## Ensure that the next stack is always the global stack.
        self._stack.setNextStack(Application.getInstance().getGlobalContainerStack())

    def getStack(self):
        return self._stack