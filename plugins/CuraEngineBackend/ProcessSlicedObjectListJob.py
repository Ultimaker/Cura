# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

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
        super().__init__()
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
        layerHeight = settings.getSettingValueByKey("layer_height")

        center = None
        if not settings.getSettingValueByKey("machine_center_is_zero"):
            center = numpy.array([settings.getSettingValueByKey("machine_width") / 2, 0.0, -settings.getSettingValueByKey("machine_depth") / 2])
        else:
            center = numpy.array([0.0, 0.0, 0.0])

        mesh = MeshData()
        for object in self._message.objects:
            try:
                node = objectIdMap[object.id]
            except KeyError:
                continue

            layerData = LayerData.LayerData()
            for layer in object.layers:
                layerData.addLayer(layer.id)
                layerData.setLayerHeight(layer.id, layer.height)
                layerData.setLayerThickness(layer.id, layer.thickness)
                for polygon in layer.polygons:
                    points = numpy.fromstring(polygon.points, dtype="i8") # Convert bytearray to numpy array
                    points = points.reshape((-1,2)) # We get a linear list of pairs that make up the points, so make numpy interpret them correctly.
                    points = numpy.asarray(points, dtype=numpy.float32)
                    points /= 1000
                    points = numpy.insert(points, 1, (layer.height / 1000), axis = 1)

                    points[:,2] *= -1

                    points -= numpy.array(center)

                    layerData.addPolygon(layer.id, polygon.type, points, polygon.line_width)

        # We are done processing all the layers we got from the engine, now create a mesh out of the data
        layerData.build()
        mesh.layerData = layerData

        new_node.setMeshData(mesh)
        new_node.setParent(self._scene.getRoot())
