# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from typing import cast, Optional
import math

from PyQt6.QtCore import QRect, QRectF, QPoint
from PyQt6.QtGui import QUndoCommand, QImage, QPainter, QPainterPath, QPen, QBrush

from UM.View.GL.Texture import Texture

from .PaintCommand import PaintCommand

class PaintStrokeCommand(PaintCommand):
    """Provides the command that does the actual painting on objects with undo/redo mechanisms"""

    PEN_OVERLAP_WIDTH = 2.5

    def __init__(self,
                 texture: Texture,
                 stroke_path: QPainterPath,
                 set_value: int,
                 bit_range: tuple[int, int],
                 mergeable: bool) -> None:
        super().__init__(texture, bit_range, make_original_image = not mergeable)

        self._stroke_path: QPainterPath = stroke_path
        self._calculateBoundingRect()
        self._set_value: int = set_value
        self._mergeable: bool = mergeable

    def id(self) -> int:
        return 0

    def redo(self) -> None:
        stroked_image, painter = self._makeClearedTexture()

        painter.setBrush(QBrush(self._set_value))
        painter.setPen(QPen(painter.brush(), self.PEN_OVERLAP_WIDTH))
        painter.setCompositionMode(QPainter.CompositionMode.RasterOp_SourceOrDestination)
        painter.drawPath(self._stroke_path)

        painter.end()

        self._texture.setSubImage(stroked_image, self._bounding_rect.left(), self._bounding_rect.top())

    def mergeWith(self, command: QUndoCommand) -> bool:
        if not isinstance(command, PaintStrokeCommand):
            return False
        paint_undo_command = cast(PaintStrokeCommand, command)

        if not paint_undo_command._mergeable:
            return False

        self._stroke_path = self._stroke_path.united(paint_undo_command._stroke_path)
        self._calculateBoundingRect()

        return True

    def _clearTextureBits(self, painter: QPainter):
        painter.setBrush(QBrush(self._getBitRangeMask()))
        painter.setPen(QPen(painter.brush(), self.PEN_OVERLAP_WIDTH))
        painter.setCompositionMode(QPainter.CompositionMode.RasterOp_NotSourceAndDestination)
        painter.drawPath(self._stroke_path)

    def _calculateBoundingRect(self):
        bounding_rect: QRectF = self._stroke_path.boundingRect()
        self._bounding_rect = QRect(
            QPoint(math.floor(bounding_rect.left()), math.floor(bounding_rect.top())),
            QPoint(math.ceil(bounding_rect.right()), math.ceil(bounding_rect.bottom())))