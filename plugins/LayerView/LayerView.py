# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.View.View import View
from UM.View.Renderer import Renderer
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Resources import Resources
from UM.Scene.Selection import Selection
from UM.Math.Color import Color

## View used to display g-code paths.
class LayerView(View):
    def __init__(self):
        super().__init__()
        self._material = None
        self._num_layers = 0
        self._layer_percentage = 0 # what percentage of layers need to be shown (SLider gives value between 0 - 100)

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

                    if self._layer_percentage < 100:
                        start = 0
                        end_layer = round(len(layer_data.getLayers()) * (self._layer_percentage / 100))
                        end = 0

                        element_counts = layer_data.getElementCounts()
                        for layer, counts in element_counts.items():
                            end += sum(counts)
                            ## Hack to ensure the end is correct. Not quite sure what causes this
                            end += 2 * len(counts)

                            if layer >= end_layer:
                                break

                        renderer.queueNode(node, mesh = layer_data, material = self._material, mode = Renderer.RenderLines, start = start, end = end, overlay = True)
                    else:
                        renderer.queueNode(node, mesh = layer_data, material = self._material, mode = Renderer.RenderLines, overlay = True)
    
    def setLayer(self, value):
        self._layer_percentage = value
        
    def endRendering(self):
        pass
