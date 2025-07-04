import copy
import json

from typing import Optional, Dict

from PyQt6.QtCore import QBuffer
from PyQt6.QtGui import QImage, QImageWriter

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
        self._texture_data_mapping: Dict[str, tuple[int, int]] = {}

    def isSliceable(self) -> bool:
        return True

    def getPaintTexture(self, create_if_required: bool = True) -> Optional[UM.View.GL.Texture.Texture]:
        if self._paint_texture is None and create_if_required:
            self._paint_texture = OpenGL.getInstance().createTexture(TEXTURE_WIDTH, TEXTURE_HEIGHT)
            image = QImage(TEXTURE_WIDTH, TEXTURE_HEIGHT, QImage.Format.Format_RGB32)
            image.fill(0)
            self._paint_texture.setImage(image)
        return self._paint_texture

    def setPaintTexture(self, texture: UM.View.GL.Texture) -> None:
        self._paint_texture = texture

    def getTextureDataMapping(self) -> Dict[str, tuple[int, int]]:
        return self._texture_data_mapping

    def setTextureDataMapping(self, mapping: Dict[str, tuple[int, int]]) -> None:
        self._texture_data_mapping = mapping

    def packTexture(self) -> Optional[bytearray]:
        if self._paint_texture is None:
            return None

        texture_image = self._paint_texture.getImage()
        if texture_image is None:
            return None

        texture_buffer = QBuffer()
        texture_buffer.open(QBuffer.OpenModeFlag.ReadWrite)
        image_writer = QImageWriter(texture_buffer, b"png")
        image_writer.setText("Description", json.dumps(self._texture_data_mapping))
        image_writer.write(texture_image)

        return texture_buffer.data()

    def __deepcopy__(self, memo) -> "SliceableObjectDecorator":
        copied_decorator = SliceableObjectDecorator()
        copied_decorator.setPaintTexture(copy.deepcopy(self.getPaintTexture(create_if_required = False)))
        copied_decorator.setTextureDataMapping(copy.deepcopy(self.getTextureDataMapping()))
        return copied_decorator
