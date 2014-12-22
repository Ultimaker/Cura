from UM.Scene.SceneNode import SceneNode
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator
from UM.Operations.TranslateOperation import TranslateOperation
from UM.Math.Float import Float
from UM.Math.Vector import Vector
from UM.Application import Application

import threading

class PlatformPhysics:
    def __init__(self, controller):
        super().__init__()
        self._controller = controller
        self._controller.activeToolChanged.connect(self._onActiveToolChanged)
        self._active_tool = None
        self._operation = False
        self._onActiveToolChanged()

    def _onActiveToolChanged(self):
        if self._active_tool:
            self._active_tool.endOperation.disconnect(self._onEndOperation)

        self._active_tool = self._controller.getActiveTool()

        if self._active_tool:
            self._active_tool.endOperation.connect(self._onEndOperation)

    def _onEndOperation(self):
        root = self._controller.getScene().getRoot()
        for node in BreadthFirstIterator(root):
            if type(node) is not SceneNode:
                continue

            bbox = node.getBoundingBox()
            if not Float.fuzzyCompare(bbox.bottom, 0.0):
                self._signal_source = node
                op = TranslateOperation(node, Vector(0, -bbox.bottom, 0))
                Application.getInstance().getOperationStack().push(op)
                self._signal_source = None
