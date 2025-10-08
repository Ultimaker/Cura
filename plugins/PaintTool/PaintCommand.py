# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Tuple, Optional, Dict

import numpy
from PyQt6.QtGui import QUndoCommand, QImage, QPainter, QBrush

from UM.View.GL.Texture import Texture
from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator


class PaintCommand(QUndoCommand):
    """Provides a command that somehow modifies the actual painting on objects with undo/redo mechanisms"""

    FULL_INT32 = 0xffffffff

    def __init__(self, texture: Texture, bit_range: tuple[int, int], make_original_image = True) -> None:
        super().__init__()

        self._texture: Texture = texture
        self._bit_range: tuple[int, int] = bit_range
        self._original_texture_image = None
        self._bounding_rect = texture.getImage().rect()

        self._texel_count_object: Optional[SliceableObjectDecorator] = None

        if make_original_image:
            self._original_texture_image = self._texture.getImage().copy()
            painter = QPainter(self._original_texture_image)

            # Keep only the bits contained in the bit range, so that we won't modify anything else in the image
            painter.setCompositionMode(QPainter.CompositionMode.RasterOp_SourceAndDestination)
            painter.fillRect(self._original_texture_image.rect(), QBrush(self._getBitRangeMask()))
            painter.end()

    def enableTexelCounting(self, texel_count_object: Optional[SliceableObjectDecorator] = None):
        self._texel_count_object = texel_count_object

    def undo(self) -> None:
        if self._original_texture_image is None:
            return

        texel_counts_before = self._countTexels()

        painter = self._makeClearedTexture()
        painter.setCompositionMode(QPainter.CompositionMode.RasterOp_SourceOrDestination)
        painter.drawImage(0, 0, self._original_texture_image)
        painter.end()

        self._pushTexelDifference(texel_counts_before)
        self._texture.updateImagePart(self._bounding_rect)

    def _pushTexelDifference(self, texel_counts_before: Dict[int, int]) -> None:
        if self._texel_count_object is None:
            return
        texel_counts_changed = {}
        texel_counts_after = self._countTexels()
        for bit in self._bit_range:
            texel_counts_changed[bit] = texel_counts_after.get(bit, 0) - texel_counts_before.get(bit, 0)
        self._texel_count_object.changeExtruderTexelCounts(texel_counts_changed)

    def _countTexels(self) -> Dict[int, int]:
        if self._texel_count_object is None:
            return {}
        return self._texture.getTexelCountsInRect(self._bounding_rect, self._bit_range)

    def _makeClearedTexture(self) -> QPainter:
        painter = QPainter(self._texture.getImage())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        self._clearTextureBits(painter)
        return painter

    def _clearTextureBits(self, painter: QPainter):
        raise NotImplementedError()

    @staticmethod
    def getBitRangeMask(bit_range: tuple[int, int]) -> int:
        bit_range_start, bit_range_end = bit_range
        return (((PaintCommand.FULL_INT32 << (32 - 1 - (bit_range_end - bit_range_start))) & PaintCommand.FULL_INT32) >>
                (32 - 1 - bit_range_end))

    def _getBitRangeMask(self) -> int:
        return PaintCommand.getBitRangeMask(self._bit_range)
