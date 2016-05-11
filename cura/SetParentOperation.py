# Copyright (c) 2016 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from UM.Scene.SceneNode import SceneNode
from UM.Operations import Operation

from UM.Math.Vector import Vector

##  An operation that parents a scene node to another scene node.

class SetParentOperation(Operation.Operation):
    ##  Initialises this SetParentOperation.
    #
    #   \param node The node which will be reparented.
    #   \param parent_node The node which will be the parent.
    def __init__(self, node, parent_node):
        super().__init__()
        self._node = node
        self._parent = parent_node
        self._old_parent = node.getParent() # To restore the previous parent in case of an undo.

    ##  Undoes the set-parent operation, restoring the old parent.
    def undo(self):
        self._set_parent(self._old_parent)

    ##  Re-applies the set-parent operation.
    def redo(self):
        self._set_parent(self._parent)

    ##  Sets the parent of the node while applying transformations to the world-transform of the node stays the same.
    #
    #   \param new_parent The new parent. Note: this argument can be None, which would hide the node from the scene.
    def _set_parent(self, new_parent):
        if new_parent:
            self._node.setPosition(self._node.getWorldPosition() - new_parent.getWorldPosition())
            current_parent = self._node.getParent()
            if current_parent:
                self._node.scale(current_parent.getScale() / new_parent.getScale())
                self._node.rotate(current_parent.getOrientation())
            else:
                self._node.scale(Vector(1, 1, 1) / new_parent.getScale())
            self._node.rotate(new_parent.getOrientation().getInverse())

        self._node.setParent(new_parent)

    ##  Returns a programmer-readable representation of this operation.
    #
    #   \return A programmer-readable representation of this operation.
    def __repr__(self):
        return "SetParentOperation(node = {0}, parent_node={1})".format(self._node, self._parent)
