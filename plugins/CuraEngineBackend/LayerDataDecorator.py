from UM.Scene.SceneNodeDecorator import SceneNodeDecorator

class LayerDataDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()
        self._layer_data = None
        
    def getLayerData(self):
        return self._layer_data
    
    def setLayerData(self, layer_data):
        self._layer_data = layer_data