# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Tuple, Optional, Dict

import numpy
from PyQt6.QtGui import QUndoCommand, QImage, QPainter, QBrush

from UM.View.GL.Texture import Texture
from cura.CuraApplication import CuraApplication
from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator


class PaintCommand(QUndoCommand):
    """Provides a command that somehow modifies the actual painting on objects with undo/redo mechanisms"""

    FULL_INT32 = 0xffffffff

    def __init__(self,
                 texture: Texture,
                 bit_range: tuple[int, int],
                 make_original_image = True,
                 sliceable_object_decorator: Optional[SliceableObjectDecorator] = None) -> None:
        super().__init__()

        self._texture: Texture = texture
        self._bit_range: tuple[int, int] = bit_range
        self._original_texture_image = None
        self._bounding_rect = texture.getImage().rect()

        self._sliceable_object_decorator: Optional[SliceableObjectDecorator] = sliceable_object_decorator

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

        painter = self._makeClearedTexture(extended=True)
        painter.setCompositionMode(QPainter.CompositionMode.RasterOp_SourceOrDestination)
        painter.drawImage(0, 0, self._original_texture_image)
        painter.end()

        self._setPaintedExtrudersCountDirty()
        self._texture.updateImagePart(self._bounding_rect)

    def _setPaintedExtrudersCountDirty(self) -> None:
        if self._sliceable_object_decorator is not None:
            self._sliceable_object_decorator.setPaintedExtrudersCountDirty()

    def _makeClearedTexture(self, extended = False) -> QPainter:
        painter = QPainter(self._texture.getImage())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        self._clearTextureBits(painter, extended)
        return painter

    def _clearTextureBits(self, painter: QPainter, extended = False):
        raise NotImplementedError()

    @staticmethod
    def getBitRangeMask(bit_range: tuple[int, int]) -> int:
        bit_range_start, bit_range_end = bit_range
        return (((PaintCommand.FULL_INT32 << (32 - 1 - (bit_range_end - bit_range_start))) & PaintCommand.FULL_INT32) >>
                (32 - 1 - bit_range_end))

    def _getBitRangeMask(self) -> int:
        return PaintCommand.getBitRangeMask(self._bit_range)
