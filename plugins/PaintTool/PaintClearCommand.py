# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional

from PyQt6.QtGui import QUndoCommand, QImage, QPainter, QBrush

from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator
from UM.View.GL.Texture import Texture

from .PaintCommand import PaintCommand


class PaintClearCommand(PaintCommand):
    """Provides the command that clears all the painting for the current mode"""

    def __init__(self,
                 texture: Texture,
                 bit_range: tuple[int, int],
                 set_value: int,
                 sliceable_object_decorator: Optional[SliceableObjectDecorator] = None) -> None:
        super().__init__(texture, bit_range, sliceable_object_decorator=sliceable_object_decorator)
        self._set_value = set_value

    def id(self) -> int:
        return 1

    def redo(self) -> None:
        painter = self._makeClearedTexture()
        if self._set_value > 0:
            painter.setCompositionMode(QPainter.CompositionMode.RasterOp_SourceOrDestination)
            painter.fillRect(self._texture.getImage().rect(), QBrush(self._set_value))
        painter.end()

        self._setPaintedExtrudersCountDirty()
        self._texture.updateImagePart(self._bounding_rect)

    def mergeWith(self, command: QUndoCommand) -> bool:
        if not isinstance(command, PaintClearCommand):
            return False

        # There is actually nothing more to do here, both clear commands already have the same original texture
        return True

    def _clearTextureBits(self, painter: QPainter, extended = False):
        painter.setCompositionMode(QPainter.CompositionMode.RasterOp_NotSourceAndDestination)
        painter.fillRect(self._texture.getImage().rect(), QBrush(self._getBitRangeMask()))