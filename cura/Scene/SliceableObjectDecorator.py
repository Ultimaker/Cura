import copy
import json

from typing import Optional, Dict

from PyQt6.QtCore import QBuffer
from PyQt6.QtGui import QImage, QImageWriter

from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
from UM.View.GL.OpenGL import OpenGL
from UM.View.GL.Texture import Texture
from UM.Signal import Signal


class SliceableObjectDecorator(SceneNodeDecorator):
    def __init__(self) -> None:
        super().__init__()
        self._paint_texture = None
        self._texture_data_mapping: Dict[str, tuple[int, int]] = {}

        self.paintTextureChanged = Signal()

    def isSliceable(self) -> bool:
        return True

    def getPaintTexture(self) -> Optional[Texture]:
        return self._paint_texture

    def getPaintTextureChangedSignal(self) -> Signal:
        return self.paintTextureChanged

    def setPaintTexture(self, texture: Texture) -> None:
        self._paint_texture = texture
        self.paintTextureChanged.emit()

    def getTextureDataMapping(self) -> Dict[str, tuple[int, int]]:
        return self._texture_data_mapping

    def setTextureDataMapping(self, mapping: Dict[str, tuple[int, int]]) -> None:
        self._texture_data_mapping = mapping

    def prepareTexture(self, width: int, height: int) -> None:
        if self._paint_texture is None:
            self._paint_texture = OpenGL.getInstance().createTexture(width, height)
            image = QImage(width, height, QImage.Format.Format_RGB32)
            image.fill(0)
            self._paint_texture.setImage(image)
            self.paintTextureChanged.emit()

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
        copied_decorator.setPaintTexture(copy.deepcopy(self.getPaintTexture()))
        copied_decorator.setTextureDataMapping(copy.deepcopy(self.getTextureDataMapping()))
        return copied_decorator
