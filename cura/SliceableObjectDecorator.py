from UM.Scene.SceneNodeDecorator import SceneNodeDecorator


## Simple decorator to indicate a scene node is sliceable or not.
class SliceableObjectDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()
        self._sliceable = True
        self._block_slicing = False
        
    def isSliceable(self):
        return self._sliceable

    def setSliceable(self, sliceable):
        self._sliceable = sliceable

    def shouldBlockSlicing(self):
        return self._block_slicing

    def setBlockSlicing(self, block_slicing):
        self._block_slicing = block_slicing
