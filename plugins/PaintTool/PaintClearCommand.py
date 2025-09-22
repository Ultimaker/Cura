# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional

from PyQt6.QtGui import QUndoCommand, QImage, QPainter, QBrush

from UM.View.GL.Texture import Texture

from .PaintCommand import PaintCommand


class PaintClearCommand(PaintCommand):
    """Provides the command that clear all the painting for the current mode"""

    def __init__(self, texture: Texture, bit_range: tuple[int, int]) -> None:
        super().__init__(texture, bit_range)

        self._original_texture_image: Optional[QImage] = texture.getImage().copy()

        self._cleared_texture = self._original_texture_image.copy()
        painter = QPainter(self._cleared_texture)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setCompositionMode(QPainter.CompositionMode.RasterOp_SourceAndDestination)
        painter.fillRect(self._cleared_texture.rect(), QBrush(self._getClearTextureBitMask()))

        painter.end()

    def id(self) -> int:
        return 1

    def redo(self) -> None:
        self._texture.setSubImage(self._cleared_texture, 0, 0)

    def undo(self) -> None:
        self._texture.setSubImage(self._original_texture_image, 0, 0)

    def mergeWith(self, command: QUndoCommand) -> bool:
        if not isinstance(command, PaintClearCommand):
            return False

        # There is actually nothing more to do here, both clear commands already have the same original texture
        return True
