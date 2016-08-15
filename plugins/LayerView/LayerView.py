# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.View.View import View
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Resources import Resources
from UM.Event import Event, KeyEvent
from UM.Signal import Signal
from UM.Scene.Selection import Selection
from UM.Math.Color import Color
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Job import Job
from UM.Preferences import Preferences
from UM.Logger import Logger

from UM.View.RenderBatch import RenderBatch
from UM.View.GL.OpenGL import OpenGL

from cura.ConvexHullNode import ConvexHullNode

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication

from . import LayerViewProxy

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

import numpy

## View used to display g-code paths.
class LayerView(View):
    def __init__(self):
        super().__init__()
        self._shader = None
        self._selection_shader = None
        self._num_layers = 0
        self._layer_percentage = 0  # what percentage of layers need to be shown (Slider gives value between 0 - 100)
        self._proxy = LayerViewProxy.LayerViewProxy()
        self._controller.getScene().getRoot().childrenChanged.connect(self._onSceneChanged)
        self._max_layers = 0
        self._current_layer_num = 0
        self._current_layer_mesh = None
        self._current_layer_jumps = None
        self._top_layers_job = None
        self._activity = False
        self._old_max_layers = 0

        Preferences.getInstance().addPreference("view/top_layer_count", 5)
        Preferences.getInstance().addPreference("view/only_show_top_layers", False)
        Preferences.getInstance().preferenceChanged.connect(self._onPreferencesChanged)

        self._solid_layers = int(Preferences.getInstance().getValue("view/top_layer_count"))
        self._only_show_top_layers = bool(Preferences.getInstance().getValue("view/only_show_top_layers"))
        self._busy = False

    def getActivity(self):
        return self._activity

    def getCurrentLayer(self):
        return self._current_layer_num

    def _onSceneChanged(self, node):
        self.calculateMaxLayers()

    def getMaxLayers(self):
        return self._max_layers

    busyChanged = Signal()

    def isBusy(self):
        return self._busy

    def setBusy(self, busy):
        if busy != self._busy:
            self._busy = busy
            self.busyChanged.emit()

    def resetLayerData(self):
        self._current_layer_mesh = None
        self._current_layer_jumps = None

    def beginRendering(self):
        scene = self.getController().getScene()
        renderer = self.getRenderer()

        if not self._selection_shader:
            self._selection_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "color.shader"))
            self._selection_shader.setUniformValue("u_color", Color(32, 32, 32, 128))

        for node in DepthFirstIterator(scene.getRoot()):
            # We do not want to render ConvexHullNode as it conflicts with the bottom layers.
            # However, it is somewhat relevant when the node is selected, so do render it then.
            if type(node) is ConvexHullNode and not Selection.isSelected(node.getWatchedNode()):
                continue

            if not node.render(renderer):
                if node.getMeshData() and node.isVisible():
                    if Selection.isSelected(node):
                        renderer.queueNode(node, transparent = True, shader = self._selection_shader)
                    layer_data = node.callDecoration("getLayerData")
                    if not layer_data:
                        continue

                    # Render all layers below a certain number as line mesh instead of vertices.
                    if self._current_layer_num - self._solid_layers > -1 and not self._only_show_top_layers:
                        start = 0
                        end = 0
                        element_counts = layer_data.getElementCounts()
                        for layer, counts in element_counts.items():
                            if layer + self._solid_layers > self._current_layer_num:
                                break
                            end += counts

                        # This uses glDrawRangeElements internally to only draw a certain range of lines.
                        renderer.queueNode(node, mesh = layer_data, mode = RenderBatch.RenderMode.Lines, range = (start, end))

                    if self._current_layer_mesh:
                        renderer.queueNode(node, mesh = self._current_layer_mesh)

                    if self._current_layer_jumps:
                        renderer.queueNode(node, mesh = self._current_layer_jumps)

    def setLayer(self, value):
        if self._current_layer_num != value:
            self._current_layer_num = value
            if self._current_layer_num < 0:
                self._current_layer_num = 0
            if self._current_layer_num > self._max_layers:
                self._current_layer_num = self._max_layers

            self._startUpdateTopLayers()

            self.currentLayerNumChanged.emit()

    def calculateMaxLayers(self):
        scene = self.getController().getScene()
        self._activity = True

        self._old_max_layers = self._max_layers
        ## Recalculate num max layers
        new_max_layers = 0
        for node in DepthFirstIterator(scene.getRoot()):
            layer_data = node.callDecoration("getLayerData")
            if not layer_data:
                continue

            if new_max_layers < len(layer_data.getLayers()):
                new_max_layers = len(layer_data.getLayers()) - 1

        if new_max_layers > 0 and new_max_layers != self._old_max_layers:
            self._max_layers = new_max_layers

            # The qt slider has a bit of weird behavior that if the maxvalue needs to be changed first
            # if it's the largest value. If we don't do this, we can have a slider block outside of the
            # slider. 
            if new_max_layers > self._current_layer_num:
                self.maxLayersChanged.emit()
                self.setLayer(int(self._max_layers))
            else:
                self.setLayer(int(self._max_layers))
                self.maxLayersChanged.emit()
        self._startUpdateTopLayers()

    maxLayersChanged = Signal()
    currentLayerNumChanged = Signal()

    ##  Hackish way to ensure the proxy is already created, which ensures that the layerview.qml is already created
    #   as this caused some issues. 
    def getProxy(self, engine, script_engine):
        return self._proxy

    def endRendering(self):
        pass

    def event(self, event):
        modifiers = QApplication.keyboardModifiers()
        ctrl_is_active = modifiers == Qt.ControlModifier
        if event.type == Event.KeyPressEvent and ctrl_is_active:
            if event.key == KeyEvent.UpKey:
                self.setLayer(self._current_layer_num + 1)
                return True
            if event.key == KeyEvent.DownKey:
                self.setLayer(self._current_layer_num - 1)
                return True

    def _startUpdateTopLayers(self):
        if self._top_layers_job:
            self._top_layers_job.finished.disconnect(self._updateCurrentLayerMesh)
            self._top_layers_job.cancel()

        self.setBusy(True)

        self._top_layers_job = _CreateTopLayersJob(self._controller.getScene(), self._current_layer_num, self._solid_layers)
        self._top_layers_job.finished.connect(self._updateCurrentLayerMesh)
        self._top_layers_job.start()

    def _updateCurrentLayerMesh(self, job):
        self.setBusy(False)

        if not job.getResult():
            return
        self.resetLayerData()  # Reset the layer data only when job is done. Doing it now prevents "blinking" data.
        self._current_layer_mesh = job.getResult().get("layers")
        self._current_layer_jumps = job.getResult().get("jumps")
        self._controller.getScene().sceneChanged.emit(self._controller.getScene().getRoot())

        self._top_layers_job = None

    def _onPreferencesChanged(self, preference):
        if preference != "view/top_layer_count" and preference != "view/only_show_top_layers":
            return

        self._solid_layers = int(Preferences.getInstance().getValue("view/top_layer_count"))
        self._only_show_top_layers = bool(Preferences.getInstance().getValue("view/only_show_top_layers"))

        self._startUpdateTopLayers()


class _CreateTopLayersJob(Job):
    def __init__(self, scene, layer_number, solid_layers):
        super().__init__()

        self._scene = scene
        self._layer_number = layer_number
        self._solid_layers = solid_layers
        self._cancel = False

    def run(self):
        layer_data = None
        for node in DepthFirstIterator(self._scene.getRoot()):
            layer_data = node.callDecoration("getLayerData")
            if layer_data:
                break

        if self._cancel or not layer_data:
            return

        layer_mesh = MeshBuilder()
        for i in range(self._solid_layers):
            layer_number = self._layer_number - i
            if layer_number < 0:
                continue

            try:
                layer = layer_data.getLayer(layer_number).createMesh()
            except Exception:
                Logger.logException("w", "An exception occurred while creating layer mesh.")
                return

            if not layer or layer.getVertices() is None:
                continue

            layer_mesh.addIndices(layer_mesh.getVertexCount() + layer.getIndices())
            layer_mesh.addVertices(layer.getVertices())

            # Scale layer color by a brightness factor based on the current layer number
            # This will result in a range of 0.5 - 1.0 to multiply colors by.
            brightness = numpy.ones((1, 4), dtype=numpy.float32) * (2.0 - (i / self._solid_layers)) / 2.0
            brightness[0, 3] = 1.0
            layer_mesh.addColors(layer.getColors() * brightness)

            if self._cancel:
                return

            Job.yieldThread()

        if self._cancel:
            return

        Job.yieldThread()
        jump_mesh = layer_data.getLayer(self._layer_number).createJumps()
        if not jump_mesh or jump_mesh.getVertices() is None:
            jump_mesh = None

        self.setResult({"layers": layer_mesh.build(), "jumps": jump_mesh})

    def cancel(self):
        self._cancel = True
        super().cancel()
