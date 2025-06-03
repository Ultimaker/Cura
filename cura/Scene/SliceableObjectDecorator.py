import copy

from typing import Optional

import UM.View.GL.Texture
from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
from UM.View.GL.OpenGL import OpenGL
from UM.View.GL.Texture import Texture


# FIXME: When the texture UV-unwrapping is done, these two values will need to be set to a proper value (suggest 4096 for both).
TEXTURE_WIDTH = 512
TEXTURE_HEIGHT = 512

class SliceableObjectDecorator(SceneNodeDecorator):
    def __init__(self) -> None:
        super().__init__()
        self._paint_texture = None

    def isSliceable(self) -> bool:
        return True

    def getPaintTexture(self, create_if_required: bool = True) -> Optional[UM.View.GL.Texture.Texture]:
        if self._paint_texture is None and create_if_required:
            self._paint_texture = OpenGL.getInstance().createTexture(TEXTURE_WIDTH, TEXTURE_HEIGHT)
        return self._paint_texture

    def setPaintTexture(self, texture: UM.View.GL.Texture) -> None:
        self._paint_texture = texture

    def __deepcopy__(self, memo) -> "SliceableObjectDecorator":
        copied_decorator = SliceableObjectDecorator()
        copied_decorator.setPaintTexture(copy.deepcopy(self.getPaintTexture()))
        return copied_decorator
