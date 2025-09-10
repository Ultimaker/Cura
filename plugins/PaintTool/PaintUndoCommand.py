# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from typing import cast, Optional

from PyQt6.QtCore import QRect, QPoint
from PyQt6.QtGui import QUndoCommand, QImage, QPainter

from UM.View.GL.Texture import Texture


class PaintUndoCommand(QUndoCommand):
    """Provides the command that does the actual painting on objects with undo/redo mechanisms"""

    def __init__(self,
                 texture: Texture,
                 stroke_mask: QImage,
                 x: int,
                 y: int,
                 set_value: int,
                 bit_range: tuple[int, int],
                 mergeable: bool) -> None:
        super().__init__()

        self._original_texture_image: Optional[QImage] = texture.getImage().copy() if not mergeable else None
        self._texture: Texture = texture
        self._stroke_mask: QImage = stroke_mask
        self._x: int = x
        self._y: int = y
        self._set_value: int = set_value
        self._bit_range: tuple[int, int] = bit_range
        self._mergeable: bool = mergeable

    def id(self) -> int:
        # Since the undo stack will contain only commands of this type, we can use a fixed ID
        return 0

    def redo(self) -> None:
        actual_image = self._texture.getImage()

        bit_range_start, bit_range_end = self._bit_range
        full_int32 = 0xffffffff
        clear_texture_bit_mask = full_int32 ^ (((full_int32 << (32 - 1 - (bit_range_end - bit_range_start))) & full_int32) >> (
                    32 - 1 - bit_range_end))
        image_rect = QRect(0, 0, self._stroke_mask.width(), self._stroke_mask.height())

        clear_bits_image = self._stroke_mask.copy()
        clear_bits_image.invertPixels()
        painter = QPainter(clear_bits_image)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Lighten)
        painter.fillRect(image_rect, clear_texture_bit_mask)
        painter.end()

        set_value_image = self._stroke_mask.copy()
        painter = QPainter(set_value_image)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)
        painter.fillRect(image_rect, self._set_value)
        painter.end()

        stroked_image = actual_image.copy(self._x, self._y, self._stroke_mask.width(), self._stroke_mask.height())
        painter = QPainter(stroked_image)
        painter.setCompositionMode(QPainter.CompositionMode.RasterOp_SourceAndDestination)
        painter.drawImage(0, 0, clear_bits_image)
        painter.setCompositionMode(QPainter.CompositionMode.RasterOp_SourceOrDestination)
        painter.drawImage(0, 0, set_value_image)
        painter.end()

        self._texture.setSubImage(stroked_image, self._x, self._y)

    def undo(self) -> None:
        if self._original_texture_image is not None:
            self._texture.setSubImage(self._original_texture_image.copy(self._x,
                                                                        self._y,
                                                                        self._stroke_mask.width(),
                                                                        self._stroke_mask.height()),
                                      self._x,
                                      self._y)

    def mergeWith(self, command: QUndoCommand) -> bool:
        if not isinstance(command, PaintUndoCommand):
            return False
        paint_undo_command = cast(PaintUndoCommand, command)

        if not paint_undo_command._mergeable:
            return False

        self_rect = QRect(QPoint(self._x, self._y), self._stroke_mask.size())
        command_rect = QRect(QPoint(paint_undo_command._x, paint_undo_command._y), paint_undo_command._stroke_mask.size())
        bounding_rect = self_rect.united(command_rect)

        merged_mask = QImage(bounding_rect.width(), bounding_rect.height(), self._stroke_mask.format())
        merged_mask.fill(0)

        painter = QPainter(merged_mask)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Lighten)
        painter.drawImage(self._x - bounding_rect.x(), self._y - bounding_rect.y(), self._stroke_mask)
        painter.drawImage(paint_undo_command._x - bounding_rect.x(), paint_undo_command._y - bounding_rect.y(), paint_undo_command._stroke_mask)
        painter.end()

        self._x = bounding_rect.x()
        self._y = bounding_rect.y()
        self._stroke_mask = merged_mask

        return True
