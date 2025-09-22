# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt6.QtGui import QUndoCommand

from UM.View.GL.Texture import Texture


class PaintCommand(QUndoCommand):
    """Provides a command that somehow modifies the actual painting on objects with undo/redo mechanisms"""

    def __init__(self, texture: Texture, bit_range: tuple[int, int]) -> None:
        super().__init__()

        self._texture: Texture = texture
        self._bit_range: tuple[int, int] = bit_range

    def _getClearTextureBitMask(self):
        bit_range_start, bit_range_end = self._bit_range
        full_int32 = 0xffffffff
        return full_int32 ^ (((full_int32 << (32 - 1 - (bit_range_end - bit_range_start))) & full_int32) >>
                             (32 - 1 - bit_range_end))
