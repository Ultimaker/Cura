from UM.View.View import View
from UM.View.Renderer import Renderer
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Resources import Resources

class LayerView(View):
    def __init__(self):
        super().__init__()
        self._material = None

    def beginRendering(self):
        scene = self.getController().getScene()
        renderer = self.getRenderer()

        if not self._material:
            self._material = renderer.createMaterial(Resources.getPath(Resources.ShadersLocation, 'basic.vert'), Resources.getPath(Resources.ShadersLocation, 'vertexcolor.frag'))

            self._material.setUniformValue("u_color", [1.0, 0.0, 0.0, 1.0])

        for node in DepthFirstIterator(scene.getRoot()):
            if not node.render(renderer):
                if node.getMeshData() and node.isVisible():
                    try:
                        layerData = node.getMeshData().layerData
                    except AttributeError:
                        continue

                    renderer.queueNode(node, mesh = layerData, material = self._material, mode = Renderer.RenderLines)

    def endRendering(self):
        pass
