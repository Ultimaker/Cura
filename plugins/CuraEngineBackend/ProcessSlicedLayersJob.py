# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Job import Job
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Application import Application
from UM.Mesh.MeshData import MeshData

from UM.Message import Message
from UM.i18n import i18nCatalog

from UM.Math.Vector import Vector

from cura import LayerData
from cura import LayerDataDecorator

import numpy
import struct

catalog = i18nCatalog("cura")

class ProcessSlicedLayersJob(Job):
    def __init__(self, layers):
        super().__init__()
        self._layers = layers
        self._scene = Application.getInstance().getController().getScene()
        self._progress = None
        self._abort_requested = False

    ##  Aborts the processing of layers.
    #
    #   This abort is made on a best-effort basis, meaning that the actual
    #   job thread will check once in a while to see whether an abort is
    #   requested and then stop processing by itself. There is no guarantee
    #   that the abort will stop the job any time soon or even at all.
    def abort(self):
        self._abort_requested = True

    def run(self):
        if Application.getInstance().getController().getActiveView().getPluginId() == "LayerView":
            self._progress = Message(catalog.i18nc("@info:status", "Processing Layers"), 0, False, -1)
            self._progress.show()
            Job.yieldThread()
            if self._abort_requested:
                if self._progress:
                    self._progress.hide()
                return

        Application.getInstance().getController().activeViewChanged.connect(self._onActiveViewChanged)

        object_id_map = {}
        new_node = SceneNode()

        ## Remove old layer data (if any)
        for node in DepthFirstIterator(self._scene.getRoot()):
            if type(node) is SceneNode and node.getMeshData():
                if node.callDecoration("getLayerData"):
                    self._scene.getRoot().removeChild(node)
            Job.yieldThread()
            if self._abort_requested:
                if self._progress:
                    self._progress.hide()
                return

        settings = Application.getInstance().getMachineManager().getWorkingProfile()

        mesh = MeshData()
        layer_data = LayerData.LayerData()
        layer_count = len(self._layers)

        current_layer = 0

        for layer in self._layers:
            layer_data.addLayer(layer.id)
            layer_data.setLayerHeight(layer.id, layer.height)
            layer_data.setLayerThickness(layer.id, layer.thickness)

            for p in range(layer.repeatedMessageCount("polygons")):
                polygon = layer.getRepeatedMessage("polygons", p)

                points = numpy.fromstring(polygon.points, dtype="i8") # Convert bytearray to numpy array
                points = points.reshape((-1,2)) # We get a linear list of pairs that make up the points, so make numpy interpret them correctly.

                # Create a new 3D-array, copy the 2D points over and insert the right height.
                # This uses manual array creation + copy rather than numpy.insert since this is
                # faster.
                new_points = numpy.empty((len(points), 3), numpy.float32)
                new_points[:,0] = points[:,0]
                new_points[:,1] = layer.height
                new_points[:,2] = -points[:,1]

                new_points /= 1000

                layer_data.addPolygon(layer.id, polygon.type, new_points, polygon.line_width)
                Job.yieldThread()
            Job.yieldThread()
            current_layer += 1
            progress = (current_layer / layer_count) * 99
            # TODO: Rebuild the layer data mesh once the layer has been processed.
            # This needs some work in LayerData so we can add the new layers instead of recreating the entire mesh.

            if self._abort_requested:
                if self._progress:
                    self._progress.hide()
                return
            if self._progress:
                self._progress.setProgress(progress)

        # We are done processing all the layers we got from the engine, now create a mesh out of the data
        layer_data.build()

        if self._abort_requested:
            if self._progress:
                self._progress.hide()
            return

        #Add layerdata decorator to scene node to indicate that the node has layerdata
        decorator = LayerDataDecorator.LayerDataDecorator()
        decorator.setLayerData(layer_data)
        new_node.addDecorator(decorator)

        new_node.setMeshData(mesh)
        new_node.setParent(self._scene.getRoot()) #Note: After this we can no longer abort!

        if not settings.getSettingValue("machine_center_is_zero"):
            new_node.setPosition(Vector(-settings.getSettingValue("machine_width") / 2, 0.0, settings.getSettingValue("machine_depth") / 2))

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
                if self._progress.getProgress() != 100:
                    self._progress.show()
            else:
                if self._progress:
                    self._progress.hide()

