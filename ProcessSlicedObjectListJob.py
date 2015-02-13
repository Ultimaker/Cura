from UM.Job import Job
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Application import Application
from UM.Mesh.MeshData import MeshData

from . import LayerData

import numpy
import struct

class ProcessSlicedObjectListJob(Job):
    def __init__(self, message, center):
        super().__init__(description = 'Processing sliced object')
        self._message = message
        self._scene = Application.getInstance().getController().getScene()
        self._center = center

    def run(self):
        objectIdMap = {}
        for node in DepthFirstIterator(self._scene.getRoot()):
            if type(node) is SceneNode and node.getMeshData():
                objectIdMap[id(node)] = node

        layerHeight = Application.getInstance().getActiveMachine().getSettingValueByKey('layer_height')

        for object in self._message.objects:
            mesh = objectIdMap[object.id].getMeshData()

            layerData = LayerData.LayerData()
            for layer in object.layers:
                for polygon in layer.polygons:
                    points = numpy.fromstring(polygon.points, dtype='i8') # Convert bytearray to numpy array
                    points = points.reshape((-1,2)) # We get a linear list of pairs that make up the points, so make numpy interpret them correctly.
                    points = numpy.asarray(points, dtype=numpy.float32)
                    points /= 1000
                    points = numpy.insert(points, 1, layer.id * layerHeight, axis = 1)
                    points[:,0] -= self._center.x
                    points[:,2] -= self._center.z
                    layerData.addPolygon(layer.id, polygon.type, points)

            mesh.layerData = layerData
