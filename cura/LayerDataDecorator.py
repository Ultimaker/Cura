from UM.Scene.SceneNodeDecorator import SceneNodeDecorator

## Simple decorator to indicate a scene node holds layer data.
class LayerDataDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()
        self._layer_data = None
        
    def getLayerData(self):
        return self._layer_data
    
    def setLayerData(self, layer_data):
        self._layer_data = layer_data