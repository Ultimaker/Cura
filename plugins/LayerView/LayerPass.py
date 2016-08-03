# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Logger import Logger
from UM.Application import Application
from UM.Resources import Resources
from UM.Preferences import Preferences
from UM.Signal import Signal
from UM.Job import Job

from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from UM.Scene.ToolHandle import ToolHandle
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.View.RenderPass import RenderPass
from UM.View.RenderBatch import RenderBatch
from UM.View.GL.OpenGL import OpenGL

import numpy

## RenderPass used to display g-code paths.
class LayerPass(RenderPass):
    def __init__(self, width, height):
        super().__init__("layerview", width, height)

        self._controller = Application.getInstance().getController()

        self._shader = None
        self._tool_handle_shader = None
        self._gl = OpenGL.getInstance().getBindingsObject()
        self._scene = self._controller.getScene()

        self._layer_view = None

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

    def setLayerView(self, layerview):
        self._layer_view = layerview

    def getActivity(self):
        return self._activity

    def getCurrentLayer(self):
        return self._current_layer_num

    def getMaxLayers(self):
        return self._max_layers

    def resetLayerData(self):
        self._current_layer_mesh = None
        self._current_layer_jumps = None

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
        scene = self._controller.getScene()
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

    def render(self):
        if not self._shader:
            self._shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "default.shader"))
        if not self._tool_handle_shader:
            self._tool_handle_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "toolhandle.shader"))

        self.bind()
        self._gl.glDisable(self._gl.GL_DEPTH_TEST)

        tool_handle_batch = RenderBatch(self._tool_handle_shader, type = RenderBatch.RenderType.Overlay)
        tool_handle_has_items = False

        for node in DepthFirstIterator(self._scene.getRoot()):
            if isinstance(node, ToolHandle):
                tool_handle_batch.addItem(node.getWorldTransformation(), mesh = node.getSolidMesh())
                tool_handle_has_items = True

            if type(node) is SceneNode and node.getMeshData() and node.isVisible():
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
                    batch = RenderBatch(self._shader, type = RenderBatch.RenderType.NoType, mode = RenderBatch.RenderMode.Lines, range = (start, end))
                    batch.addItem(node.getWorldTransformation(), layer_data)
                    batch.render(self._scene.getActiveCamera())

                # Create a new batch that is not range-limited
                batch = RenderBatch(self._shader, type = RenderBatch.RenderType.NoType, mode = RenderBatch.RenderMode.Lines)
                batch_has_items = False

                if self._current_layer_mesh:
                    batch_has_items = True
                    batch.addItem(node.getWorldTransformation(), self._current_layer_mesh)

                if self._current_layer_jumps:
                    batch_has_items = True
                    batch.addItem(node.getWorldTransformation(), self._current_layer_jumps)

                if batch_has_items:
                    batch.render(self._scene.getActiveCamera())

        # Render toolhandles on top of the layerview
        if tool_handle_has_items:
            tool_handle_batch.render(self._scene.getActiveCamera())

        self._gl.glEnable(self._gl.GL_DEPTH_TEST)
        self.release()

    def _onSceneChanged(self, node):
        self.calculateMaxLayers()

    def _startUpdateTopLayers(self):
        if self._top_layers_job:
            self._top_layers_job.finished.disconnect(self._updateCurrentLayerMesh)
            self._top_layers_job.cancel()

        self._layer_view.setBusy(True)

        self._top_layers_job = _CreateTopLayersJob(self._controller.getScene(), self._current_layer_num, self._solid_layers)
        self._top_layers_job.finished.connect(self._updateCurrentLayerMesh)
        self._top_layers_job.start()

    def _updateCurrentLayerMesh(self, job):
        self._layer_view.setBusy(False)

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
