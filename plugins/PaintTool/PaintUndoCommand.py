# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from typing import cast, Optional
import math

from PyQt6.QtCore import QRect, QPoint
from PyQt6.QtGui import QUndoCommand, QImage, QPainter, QPainterPath, QPen, QBrush

from UM.View.GL.Texture import Texture

from .PaintCommand import PaintCommand

class PaintUndoCommand(PaintCommand):
    """Provides the command that does the actual painting on objects with undo/redo mechanisms"""

    PEN_OVERLAP_WIDTH = 2.5

    def __init__(self,
                 texture: Texture,
                 stroke_path: QPainterPath,
                 set_value: int,
                 bit_range: tuple[int, int],
                 mergeable: bool) -> None:
        super().__init__(texture, bit_range)

        self._original_texture_image: Optional[QImage] = texture.getImage().copy() if not mergeable else None
        self._stroke_path: QPainterPath = stroke_path
        self._calculateBoundingRect()
        self._set_value: int = set_value
        self._mergeable: bool = mergeable

    def id(self) -> int:
        return 0

    def redo(self) -> None:
        actual_image = self._texture.getImage()

        bounding_rect = self._stroke_path.boundingRect()
        bounding_rect_rounded = QRect(QPoint(math.floor(bounding_rect.left()), math.floor(bounding_rect.top())),
                                      QPoint(math.ceil(bounding_rect.right()), math.ceil(bounding_rect.bottom())))

        stroked_image = actual_image.copy(bounding_rect_rounded)
        painter = QPainter(stroked_image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.translate(-bounding_rect.left(), -bounding_rect.top())

        painter.setBrush(QBrush(self._getClearTextureBitMask()))
        painter.setPen(QPen(painter.brush(), self.PEN_OVERLAP_WIDTH))
        painter.setCompositionMode(QPainter.CompositionMode.RasterOp_SourceAndDestination)
        painter.drawPath(self._stroke_path)

        painter.setBrush(QBrush(self._set_value))
        painter.setPen(QPen(painter.brush(), self.PEN_OVERLAP_WIDTH))
        painter.setCompositionMode(QPainter.CompositionMode.RasterOp_SourceOrDestination)
        painter.drawPath(self._stroke_path)

        painter.end()

        self._texture.setSubImage(stroked_image, bounding_rect_rounded.left(), bounding_rect_rounded.top())

    def undo(self) -> None:
        if self._original_texture_image is not None:
            self._texture.setSubImage(self._original_texture_image.copy(self._bounding_rect_rounded),
                                      self._bounding_rect_rounded.left(),
                                      self._bounding_rect_rounded.top())

    def mergeWith(self, command: QUndoCommand) -> bool:
        if not isinstance(command, PaintUndoCommand):
            return False
        paint_undo_command = cast(PaintUndoCommand, command)

        if not paint_undo_command._mergeable:
            return False

        self._stroke_path = self._stroke_path.united(paint_undo_command._stroke_path)
        self._calculateBoundingRect()

        return True

    def _calculateBoundingRect(self):
        self._bounding_rect = self._stroke_path.boundingRect()
        self._bounding_rect_rounded = QRect(
            QPoint(math.floor(self._bounding_rect.left()), math.floor(self._bounding_rect.top())),
            QPoint(math.ceil(self._bounding_rect.right()), math.ceil(self._bounding_rect.bottom())))
