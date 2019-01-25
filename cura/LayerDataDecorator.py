from typing import Optional

from UM.Scene.SceneNodeDecorator import SceneNodeDecorator

## Simple decorator to indicate a scene node holds layer data.
from cura.LayerData import LayerData


class LayerDataDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()
        self._layer_data = None  # type: Optional[LayerData]
        
    def getLayerData(self) -> Optional[LayerData]:
        return self._layer_data
    
    def setLayerData(self, layer_data: LayerData) -> None:
        self._layer_data = layer_data

    def __deepcopy__(self, memo) -> "LayerDataDecorator":
        copied_decorator = LayerDataDecorator()
        copied_decorator.setLayerData(self.getLayerData())
        return copied_decorator
