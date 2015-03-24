from UM.Scene.SceneNode import SceneNode
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator
from UM.Operations.TranslateOperation import TranslateOperation
from UM.Math.Float import Float
from UM.Math.Vector import Vector
from UM.Application import Application

from PlatformPhysicsOperation import PlatformPhysicsOperation

import time
import threading

class PlatformPhysics:
    def __init__(self, controller):
        super().__init__()
        self._controller = controller
        self._controller.getScene().sceneChanged.connect(self._onSceneChanged)
        self._signal_source = None

    def _onSceneChanged(self, source):
        root = self._controller.getScene().getRoot()
        for node in BreadthFirstIterator(root):
            if node is root or type(node) is not SceneNode:
                continue

            bbox = node.getBoundingBox()
            if not bbox or not bbox.isValid():
                continue

            if not Float.fuzzyCompare(bbox.bottom, 0.0):
                self._signal_source = node
                op = PlatformPhysicsOperation(node, Vector(0, -bbox.bottom, 0))
                Application.getInstance().getOperationStack().push(op)
                self._signal_source = None
