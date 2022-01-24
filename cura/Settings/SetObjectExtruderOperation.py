# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Scene.SceneNode import SceneNode
from UM.Operations.Operation import Operation

from cura.Settings.SettingOverrideDecorator import SettingOverrideDecorator


class SetObjectExtruderOperation(Operation):
    """Simple operation to set the extruder a certain object should be printed with."""

    def __init__(self, node: SceneNode, extruder_id: str) -> None:
        self._node = node
        self._extruder_id = extruder_id
        self._previous_extruder_id = None
        self._decorator_added = False

    def undo(self):
        if self._previous_extruder_id:
            self._node.callDecoration("setActiveExtruder", self._previous_extruder_id)

    def redo(self):
        stack = self._node.callDecoration("getStack") #Don't try to get the active extruder since it may be None anyway.
        if not stack:
            self._node.addDecorator(SettingOverrideDecorator())

        self._previous_extruder_id = self._node.callDecoration("getActiveExtruder")
        self._node.callDecoration("setActiveExtruder", self._extruder_id)
