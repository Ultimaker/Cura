# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Tuple, Optional

from PyQt6.QtCore import QRect
from PyQt6.QtGui import QUndoCommand, QImage, QPainter, QBrush

from UM.View.GL.Texture import Texture


class PaintCommand(QUndoCommand):
    """Provides a command that somehow modifies the actual painting on objects with undo/redo mechanisms"""

    FULL_INT32 = 0xffffffff

    def __init__(self, texture: Texture, bit_range: tuple[int, int], make_original_image = True) -> None:
        super().__init__()

        self._texture: Texture = texture
        self._bit_range: tuple[int, int] = bit_range
        self._original_texture_image = None
        self._bounding_rect = texture.getImage().rect()

        if make_original_image:
            self._original_texture_image, painter = (
                self._preparePainting(specific_source_image=self._texture.getImage().copy(),
                                      specific_bounding_rect=self._texture.getImage().rect()))

            # Keep only the bits contained in the bit range, so that we won't modify anything else in the image
            painter.setCompositionMode(QPainter.CompositionMode.RasterOp_SourceAndDestination)
            painter.fillRect(self._original_texture_image.rect(), QBrush(self._getBitRangeMask()))
            painter.end()

    def undo(self) -> None:
        if self._original_texture_image is None:
            return

        cleared_image, painter = self._makeClearedTexture()

        painter.setCompositionMode(QPainter.CompositionMode.RasterOp_SourceOrDestination)
        painter.drawImage(0, 0, self._original_texture_image)

        painter.end()

        self._texture.setSubImage(cleared_image, self._bounding_rect.left(), self._bounding_rect.top())

    def _makeClearedTexture(self) -> Tuple[QImage, QPainter]:
        dest_image, painter = self._preparePainting()
        self._clearTextureBits(painter)
        return dest_image, painter

    def _clearTextureBits(self, painter: QPainter):
        raise NotImplementedError()

    def _getBitRangeMask(self) -> int:
        bit_range_start, bit_range_end = self._bit_range
        return (((PaintCommand.FULL_INT32 << (32 - 1 - (bit_range_end - bit_range_start))) & PaintCommand.FULL_INT32) >>
                (32 - 1 - bit_range_end))

    def _preparePainting(self,
                         specific_source_image: Optional[QImage] = None,
                         specific_bounding_rect: Optional[QRect] = None) -> Tuple[QImage, QPainter]:
        source_image = specific_source_image if specific_source_image is not None else self._texture.getImage()
        bounding_rect = specific_bounding_rect if specific_bounding_rect is not None else self._bounding_rect

        dest_image = source_image.copy(bounding_rect)
        painter = QPainter(dest_image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.translate(-bounding_rect.left(), -bounding_rect.top())

        return dest_image, painter
