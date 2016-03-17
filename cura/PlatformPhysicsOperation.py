# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Operations.Operation import Operation
from UM.Operations.GroupedOperation import GroupedOperation

##  A specialised operation designed specifically to modify the previous operation.
class PlatformPhysicsOperation(Operation):
    def __init__(self, node, translation):
        super().__init__()
        self._node = node
        self._old_position = node.getPosition()
        self._new_position = node.getPosition() + translation
        self._always_merge = True

    def undo(self):
        self._node.setPosition(self._old_position)

    def redo(self):
        self._node.setPosition(self._new_position)

    def mergeWith(self, other):
        group = GroupedOperation()

        group.addOperation(self)
        group.addOperation(other)

        return group

    def __repr__(self):
        return "PlatformPhysicsOperation(t = {0})".format(self._position)
