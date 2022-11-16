# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from UM.Operations.Operation import Operation
from UM.Scene.Selection import Selection
from UM.Application import Application

from ..Scene.DuplicatedNode import DuplicatedNode
from ..PrintModeManager import PrintModeManager


##  An operation that removes a node and its duplicated node from the scene.
class RemoveNodesOperation(Operation):

    def __init__(self, node_dup: DuplicatedNode):
        super().__init__()
        self._node = node_dup.node
        self._node_dup = node_dup
        self._parent = node_dup.node.getParent()

        self._print_mode_manager = PrintModeManager.getInstance()

    def undo(self):
        self._node_dup.node.setParent(self._parent)
        print_mode = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "value")
        if print_mode in ["singleT0","singleT1","dual"]:
            self._node_dup.setParent(None)
        else:
            self._node_dup.setParent(self._parent)

        self._print_mode_manager.addDuplicatedNode(self._node_dup)

    def redo(self):
        old_parent = self._parent
        self._node_dup.node.setParent(None)
        self._node_dup.setParent(None)

        self._print_mode_manager.deleteDuplicatedNode(self._node_dup)

        if old_parent and old_parent.callDecoration("isGroup"):
            old_parent.callDecoration("recomputeConvexHull")

        # Hack to ensure that the _onchanged is triggered correctly.
        # We can't do it the right way as most remove changes don't need to trigger
        # a reslice (eg; removing hull nodes don't need to trigger reslice).
        try:
            Application.getInstance().getBackend().needsSlicing()
        except:
            pass
        if Selection.isSelected(self._node):  # Also remove the selection.
            Selection.remove(self._node)
