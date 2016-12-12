from UM.Scene.SceneNodeDecorator import SceneNodeDecorator


## Simple decorator to indicate a scene node is sliceable or not.
class SliceableObjectDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()
        self._sliceable = True
        
    def isSliceable(self):
        return self._sliceable

    def setSliceable(self, sliceable):
        self._sliceable = sliceable
