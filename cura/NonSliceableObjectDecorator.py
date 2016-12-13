from UM.Scene.SceneNodeDecorator import SceneNodeDecorator


class NonSliceableObjectDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()
        
    def isNonSliceable(self):
        return True
