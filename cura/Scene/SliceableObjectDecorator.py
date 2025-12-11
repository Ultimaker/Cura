from UM.Scene.SceneNodeDecorator import SceneNodeDecorator


# FIXME: When the texture UV-unwrapping is done, these two values will need to be set to a proper value (suggest 4096 for both).
TEXTURE_WIDTH = 512
TEXTURE_HEIGHT = 512

class SliceableObjectDecorator(SceneNodeDecorator):
    def __init__(self) -> None:
        super().__init__()

    def isSliceable(self) -> bool:
        return True
