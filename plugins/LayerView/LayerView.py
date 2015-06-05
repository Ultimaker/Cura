# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.View.View import View
from UM.View.Renderer import Renderer
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Resources import Resources
from UM.Event import Event, KeyEvent
from UM.Signal import Signal
from . import LayerViewProxy
from UM.Scene.Selection import Selection
from UM.Math.Color import Color

## View used to display g-code paths.
class LayerView(View):
    def __init__(self):
        super().__init__()
        self._material = None
        self._num_layers = 0
        self._layer_percentage = 0 # what percentage of layers need to be shown (SLider gives value between 0 - 100)
        self._current_layer_num = 0
        self._proxy = LayerViewProxy.LayerViewProxy()
        self._controller.getScene().sceneChanged.connect(self._onSceneChanged)
        self._max_layers = 10

    def getCurrentLayer(self):
        return self._current_layer_num
    
    def _onSceneChanged(self, node):
        self.calculateMaxLayers()
    
    def getMaxLayers(self):
        return self._max_layers

    def beginRendering(self):
        scene = self.getController().getScene()
        renderer = self.getRenderer()
        renderer.setRenderSelection(False)

        if not self._material:
            self._material = renderer.createMaterial(Resources.getPath(Resources.ShadersLocation, "basic.vert"), Resources.getPath(Resources.ShadersLocation, "vertexcolor.frag"))
            self._material.setUniformValue("u_color", [1.0, 0.0, 0.0, 1.0])

            self._selection_material = renderer.createMaterial(Resources.getPath(Resources.ShadersLocation, "basic.vert"), Resources.getPath(Resources.ShadersLocation, "color.frag"))
            self._selection_material.setUniformValue("u_color", Color(35, 35, 35, 128))

        for node in DepthFirstIterator(scene.getRoot()):
            if not node.render(renderer):
                if node.getMeshData() and node.isVisible():
                    if Selection.isSelected(node):
                        renderer.queueNode(node, material = self._selection_material, transparent = True)

                    try:
                        layer_data = node.getMeshData().layerData
                    except AttributeError:
                        continue

                    start = 0
                    end = 0

                    element_counts = layer_data.getElementCounts()
                    for layer, counts in element_counts.items():
                        end += sum(counts)
                        ## Hack to ensure the end is correct. Not quite sure what causes this
                        end += 2 * len(counts)

                        if layer >= self._current_layer_num:
                            break

                    renderer.queueNode(node, mesh = layer_data, material = self._material, mode = Renderer.RenderLines, start = start, end = end)

    def setLayer(self, value):
        if self._current_layer_num != value:
            self._current_layer_num = value
            if self._current_layer_num < 0:
                self._current_layer_num = 0
            if self._current_layer_num > self._max_layers:
                self._current_layer_num = self._max_layers
            self.currentLayerNumChanged.emit()
    
    currentLayerNumChanged = Signal()
    
    def calculateMaxLayers(self):
        scene = self.getController().getScene()
        renderer = self.getRenderer()
        if renderer and self._material:
            renderer.setRenderSelection(False)
            self._old_max_layers = self._max_layers
            ## Recalculate num max layers
            self._max_layers = 0
            for node in DepthFirstIterator(scene.getRoot()):
                if not node.render(renderer):
                    if node.getMeshData() and node.isVisible():
                        try:
                            layer_data = node.getMeshData().layerData
                        except AttributeError:
                            continue
                        if self._max_layers < len(layer_data.getLayers()):
                            self._max_layers = len(layer_data.getLayers())
            
            if self._max_layers != self._old_max_layers:
                self.maxLayersChanged.emit()
    
    maxLayersChanged = Signal()
    
    ##  Hackish way to ensure the proxy is already created, which ensures that the layerview.qml is already created
    #   as this caused some issues. 
    def getProxy(self, engine, script_engine):
        return self._proxy
    
    def endRendering(self):
        pass
    
    def event(self, event):
        if event.type == Event.KeyPressEvent:
            if event.key == KeyEvent.UpKey:
                self.setLayer(self._current_layer_num + 1)
            if event.key == KeyEvent.DownKey:
                self.setLayer(self._current_layer_num - 1)
