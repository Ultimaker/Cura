# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional
from UM.Scene.SceneNodeDecorator import SceneNodeDecorator

from cura.LayerData import LayerData


## Simple decorator to indicate a scene node holds layer data.
class LayerDataDecorator(SceneNodeDecorator):
    def __init__(self) -> None:
        super().__init__()
        self._layer_data = None  # type: Optional[LayerData]

    def getLayerData(self) -> Optional["LayerData"]:
        return self._layer_data

    def setLayerData(self, layer_data: LayerData) -> None:
        self._layer_data = layer_data

    def __deepcopy__(self, memo) -> "LayerDataDecorator":
        copied_decorator = LayerDataDecorator()
        copied_decorator._layer_data = self._layer_data
        return copied_decorator
