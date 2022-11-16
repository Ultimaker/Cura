# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from UM.Application import Application
from UM.Operations.Operation import Operation
from UM.Scene.Selection import Selection
from UM.Scene.SceneNode import SceneNode

from ..Scene.DuplicatedNode import DuplicatedNode
from ..PrintModeManager import PrintModeManager

from typing import Optional


##  Operation that adds a new node and its duplicated node to the scene.
class AddNodesOperation(Operation):

    def __init__(self, node_dup: DuplicatedNode, parent: Optional[SceneNode]):
        super().__init__()
        self._node = node_dup.node
        self._node_dup = node_dup
        self._parent = parent
        self._selected = False  # Was the node selected while the operation is undone? If so, we must re-select it when redoing it.

        self._print_mode_manager = PrintModeManager.getInstance()

    def undo(self):
        self._node.setParent(None)
        self._node_dup.setParent(None)
        self._selected = Selection.isSelected(self._node)
        if self._selected:
            Selection.remove(self._node)  # Also remove the node from the selection.

        self._print_mode_manager.deleteDuplicatedNode(self._node_dup)

    def redo(self):
        self._node.setParent(self._parent)
        print_mode = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "value")
        if print_mode in ["singleT0", "singleT1", "dual"]:
            self._node_dup.setParent(None)
        else:
            self._node_dup.setParent(self._parent)
        if self._selected:  # It was selected while the operation was undone. We should restore that selection.
            Selection.add(self._node)

        self._print_mode_manager.addDuplicatedNode(self._node_dup)
