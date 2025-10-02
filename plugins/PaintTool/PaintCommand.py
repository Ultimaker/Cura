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
            self._original_texture_image = self._texture.getImage().copy()
            painter = QPainter(self._original_texture_image)

            # Keep only the bits contained in the bit range, so that we won't modify anything else in the image
            painter.setCompositionMode(QPainter.CompositionMode.RasterOp_SourceAndDestination)
            painter.fillRect(self._original_texture_image.rect(), QBrush(self._getBitRangeMask()))
            painter.end()

    def undo(self) -> None:
        if self._original_texture_image is None:
            return

        painter = self._makeClearedTexture()
        painter.setCompositionMode(QPainter.CompositionMode.RasterOp_SourceOrDestination)
        painter.drawImage(0, 0, self._original_texture_image)
        painter.end()

        self._texture.updateImagePart(self._bounding_rect)

    def _makeClearedTexture(self) -> QPainter:
        painter = QPainter(self._texture.getImage())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        self._clearTextureBits(painter)
        return painter

    def _clearTextureBits(self, painter: QPainter):
        raise NotImplementedError()

    def _getBitRangeMask(self) -> int:
        bit_range_start, bit_range_end = self._bit_range
        return (((PaintCommand.FULL_INT32 << (32 - 1 - (bit_range_end - bit_range_start))) & PaintCommand.FULL_INT32) >>
                (32 - 1 - bit_range_end))
