# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Job import Job
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Application import Application
from UM.Mesh.MeshData import MeshData

from UM.Message import Message
from UM.i18n import i18nCatalog

from cura import LayerData
from cura import LayerDataDecorator

import numpy
import struct

catalog = i18nCatalog("cura")

class ProcessSlicedObjectListJob(Job):
    def __init__(self, message):
        super().__init__()
        self._message = message
        self._scene = Application.getInstance().getController().getScene()
        self._progress = None

    def run(self):
        if Application.getInstance().getController().getActiveView().getPluginId() == "LayerView":
            self._progress = Message(catalog.i18nc("@info:status", "Processing Layers"), 0, False, -1)
            self._progress.show()

        Application.getInstance().getController().activeViewChanged.connect(self._onActiveViewChanged)

        object_id_map = {}
        new_node = SceneNode()
        ## Put all nodes in a dict identified by ID
        for node in DepthFirstIterator(self._scene.getRoot()):
            if type(node) is SceneNode and node.getMeshData():
                if node.callDecoration("getLayerData"):
                    self._scene.getRoot().removeChild(node)
                else:
                    object_id_map[id(node)] = node
            Job.yieldThread()

        settings = Application.getInstance().getMachineManager().getActiveProfile()

        center = None
        if not settings.getSettingValue("machine_center_is_zero"):
            center = numpy.array([settings.getSettingValue("machine_width") / 2, 0.0, -settings.getSettingValue("machine_depth") / 2])
        else:
            center = numpy.array([0.0, 0.0, 0.0])

        mesh = MeshData()
        layer_data = LayerData.LayerData()

        layer_count = 0
        for i in range(self._message.repeatedMessageCount("objects")):
            layer_count += self._message.getRepeatedMessage("objects", i).repeatedMessageCount("layers")

        current_layer = 0
        for i in range(self._message.repeatedMessageCount("objects")):
            object = self._message.getRepeatedMessage("objects", i)
            try:
                node = object_id_map[object.id]
            except KeyError:
                continue

            for l in range(object.repeatedMessageCount("layers")):
                layer = object.getRepeatedMessage("layers", l)

                layer_data.addLayer(layer.id)
                layer_data.setLayerHeight(layer.id, layer.height)
                layer_data.setLayerThickness(layer.id, layer.thickness)

                for p in range(layer.repeatedMessageCount("polygons")):
                    polygon = layer.getRepeatedMessage("polygons", p)

                    points = numpy.fromstring(polygon.points, dtype="i8") # Convert bytearray to numpy array
                    points = points.reshape((-1,2)) # We get a linear list of pairs that make up the points, so make numpy interpret them correctly.
                    points = numpy.asarray(points, dtype=numpy.float32)
                    points /= 1000
                    points = numpy.insert(points, 1, (layer.height / 1000), axis = 1)

                    points[:,2] *= -1

                    points -= center

                    layer_data.addPolygon(layer.id, polygon.type, points, polygon.line_width)

                current_layer += 1
                progress = (current_layer / layer_count) * 100
                # TODO: Rebuild the layer data mesh once the layer has been processed.
                # This needs some work in LayerData so we can add the new layers instead of recreating the entire mesh.

                if self._progress:
                    self._progress.setProgress(progress)

        # We are done processing all the layers we got from the engine, now create a mesh out of the data
        layer_data.build()

        #Add layerdata decorator to scene node to indicate that the node has layerdata
        decorator = LayerDataDecorator.LayerDataDecorator()
        decorator.setLayerData(layer_data)
        new_node.addDecorator(decorator)

        new_node.setMeshData(mesh)
        new_node.setParent(self._scene.getRoot())

        if self._progress:
            self._progress.setProgress(100)

        view = Application.getInstance().getController().getActiveView()
        if view.getPluginId() == "LayerView":
            view.resetLayerData()

        if self._progress:
            self._progress.hide()

    def _onActiveViewChanged(self):
        if self.isRunning():
            if Application.getInstance().getController().getActiveView().getPluginId() == "LayerView":
                if not self._progress:
                    self._progress = Message(catalog.i18nc("@info:status", "Processing Layers"), 0, False, 0)
                    self._progress.show()
            else:
                if self._progress:
                    self._progress.hide()

