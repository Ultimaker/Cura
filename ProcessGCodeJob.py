from UM.Job import Job
from UM.Application import Application
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode

import os

class ProcessGCodeJob(Job):
    def __init__(self, message):
        super().__init__()

        self._scene = Application.getInstance().getController().getScene()
        self._message = message

    def run(self):
        objectIdMap = {}
        for node in DepthFirstIterator(self._scene.getRoot()):
            if type(node) is SceneNode and node.getMeshData():
                objectIdMap[id(node)] = node

        node = objectIdMap[self._message.id]
        if node:
            with open(self._message.filename) as f:
                data = f.read(None)
                setattr(node.getMeshData(), 'gcode', data)

            os.remove(self._message.filename)
