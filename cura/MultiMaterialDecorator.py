from UM.Scene.SceneNodeDecorator import SceneNodeDecorator

class MultiMaterialDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()
        
    def isMultiMaterial(self):
        return True