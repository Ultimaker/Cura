# Copyright (c) 2016 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.
from typing import Optional

from UM.Scene.SceneNode import SceneNode
from UM.Operations import Operation

from UM.Math.Vector import Vector


##  An operation that parents a scene node to another scene node.
class SetParentOperation(Operation.Operation):
    ##  Initialises this SetParentOperation.
    #
    #   \param node The node which will be reparented.
    #   \param parent_node The node which will be the parent.
    def __init__(self, node: SceneNode, parent_node: Optional[SceneNode]) -> None:
        super().__init__()
        self._node = node
        self._parent = parent_node
        self._old_parent = node.getParent() # To restore the previous parent in case of an undo.

    ##  Undoes the set-parent operation, restoring the old parent.
    def undo(self) -> None:
        self._set_parent(self._old_parent)

    ##  Re-applies the set-parent operation.
    def redo(self) -> None:
        self._set_parent(self._parent)

    ##  Sets the parent of the node while applying transformations to the world-transform of the node stays the same.
    #
    #   \param new_parent The new parent. Note: this argument can be None, which would hide the node from the scene.
    def _set_parent(self, new_parent: Optional[SceneNode]) -> None:
        if new_parent:
            current_parent = self._node.getParent()
            if current_parent:
                # Special casing for groups that have been removed.
                # In that case we want to put them back where they belong before checking the depth difference.
                # If we don't, we always get 0.
                old_parent = new_parent.callDecoration("getOldParent")
                if old_parent:
                    new_parent.callDecoration("getNode").setParent(old_parent)

                # Based on the depth difference, we need to do something different.
                depth_difference = current_parent.getDepth() - new_parent.getDepth()
                child_transformation = self._node.getLocalTransformation()
                if depth_difference > 0:
                    parent_transformation = current_parent.getLocalTransformation()
                    # A node in the chain was removed, so we need to squash the parent info into all the nodes, so positions remain the same.
                    self._node.setTransformation(parent_transformation.multiply(child_transformation))
                else:
                    # A node is inserted into the chain, so use the inverse of the parent to set the transformation of it's children.
                    parent_transformation = new_parent.getLocalTransformation()
                    result = parent_transformation.getInverse().multiply(child_transformation, copy = True)
                    self._node.setTransformation(result)

        self._node.setParent(new_parent)

    ##  Returns a programmer-readable representation of this operation.
    #
    #   \return A programmer-readable representation of this operation.
    def __repr__(self) -> str:
        return "SetParentOperation(node = {0}, parent_node={1})".format(self._node, self._parent)
