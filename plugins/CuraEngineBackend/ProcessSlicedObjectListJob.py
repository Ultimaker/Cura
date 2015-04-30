from UM.Job import Job
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Application import Application
from UM.Mesh.MeshData import MeshData

from . import LayerData

import numpy
import struct

class ProcessSlicedObjectListJob(Job):
    def __init__(self, message):
        super().__init__(description = 'Processing sliced object')
        self._message = message
        self._scene = Application.getInstance().getController().getScene()

    def run(self):
        objectIdMap = {}
        new_node = SceneNode()
        ## Put all nodes in a dict identified by ID
        for node in DepthFirstIterator(self._scene.getRoot()):
            if type(node) is SceneNode and node.getMeshData():
                if hasattr(node.getMeshData(), "layerData"):
                    self._scene.getRoot().removeChild(node)
                else:
                    objectIdMap[id(node)] = node

        settings = Application.getInstance().getActiveMachine()
        layerHeight = settings.getSettingValueByKey('layer_height')

        for object in self._message.objects:
            try:        
                node = objectIdMap[object.id]
            except KeyError:
                continue
            
            mesh = MeshData()

            layerData = LayerData.LayerData()
            for layer in object.layers:
                for polygon in layer.polygons:
                    points = numpy.fromstring(polygon.points, dtype='i8') # Convert bytearray to numpy array
                    points = points.reshape((-1,2)) # We get a linear list of pairs that make up the points, so make numpy interpret them correctly.
                    points = numpy.asarray(points, dtype=numpy.float32)
                    points /= 1000
                    points = numpy.insert(points, 1, layer.id * layerHeight, axis = 1)

                    points[:,2] *= -1

                    if not settings.getSettingValueByKey('machine_center_is_zero'):
                        center = [settings.getSettingValueByKey('machine_width') / 2, 0.0, -settings.getSettingValueByKey('machine_depth') / 2]
                        points -= numpy.array(center)

                    #points = numpy.pad(points, ((0,0), (0,1)), 'constant', constant_values=(0.0, 1.0))
                    #inverse = node.getWorldTransformation().getInverse().getData()
                    #points = points.dot(inverse)
                    #points = points[:,0:3]

                    layerData.addPolygon(layer.id, polygon.type, points)

            # We are done processing all the layers we got from the engine, now create a mesh out of the data
            layerData.build()
            mesh.layerData = layerData
            
        new_node.setMeshData(mesh)
        new_node.setParent(self._scene.getRoot())
