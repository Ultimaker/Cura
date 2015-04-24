from UM.View.View import View
from UM.View.Renderer import Renderer
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Resources import Resources

class LayerView(View):
    def __init__(self):
        super().__init__()
        self._material = None
        self._num_layers = 
        self._layer_percentage = 0 #what percentage of layers need to be shown (SLider gives value between 0 - 100)

    def beginRendering(self):
        scene = self.getController().getScene()
        renderer = self.getRenderer()
        renderer.setRenderSelection(False)
        self._num_layers = 0

        if not self._material:
            self._material = renderer.createMaterial(Resources.getPath(Resources.ShadersLocation, 'basic.vert'), Resources.getPath(Resources.ShadersLocation, 'vertexcolor.frag'))

            self._material.setUniformValue("u_color", [1.0, 0.0, 0.0, 1.0])

        for node in DepthFirstIterator(scene.getRoot()):
            if not node.render(renderer):
                if node.getMeshData() and node.isVisible():
                    try:
                        layer_data = node.getMeshData().layerData
                        if self._num_layers < len(layer_data.getLayers()):
                            self._num_layers = len(layer_data.getLayers())
                            
                    except AttributeError:
                        continue

                    renderer.queueNode(node, mesh = layer_data, material = self._material, mode = Renderer.RenderLines)
    
    def setLayer(self, value):
        self._layer_percentage = value
        
    def endRendering(self):
        pass
