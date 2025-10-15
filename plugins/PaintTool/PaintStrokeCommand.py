# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from typing import cast, Optional, List
import math

from PyQt6.QtCore import QRect, QRectF, QPoint
from PyQt6.QtGui import QUndoCommand, QImage, QPainter, QPainterPath, QPen, QBrush

from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator
from UM.View.GL.Texture import Texture
from UM.Math.Polygon import Polygon

from .PaintCommand import PaintCommand

class PaintStrokeCommand(PaintCommand):
    """Provides the command that does the actual painting on objects with undo/redo mechanisms"""

    PEN_OVERLAP_WIDTH = 2.5
    PEN_OVERLAP_WIDTH_EXTENDED = PEN_OVERLAP_WIDTH + 0.5

    def __init__(self,
                 texture: Texture,
                 stroke_polygons: List[Polygon],
                 set_value: int,
                 bit_range: tuple[int, int],
                 mergeable: bool,
                 sliceable_object_decorator: Optional[SliceableObjectDecorator] = None) -> None:
        super().__init__(texture, bit_range, make_original_image = not mergeable, sliceable_object_decorator=sliceable_object_decorator)
        self._stroke_polygons: List[Polygon] = stroke_polygons
        self._calculateBoundingRect()
        self._set_value: int = set_value
        self._mergeable: bool = mergeable

    def id(self) -> int:
        return 0

    def redo(self) -> None:
        painter = self._makeClearedTexture()
        painter.setBrush(QBrush(self._set_value))
        painter.setPen(QPen(painter.brush(), self.PEN_OVERLAP_WIDTH))
        painter.setCompositionMode(QPainter.CompositionMode.RasterOp_SourceOrDestination)
        painter.drawPath(self._makePainterPath())
        painter.end()

        self._setPaintedExtrudersCountDirty()
        self._texture.updateImagePart(self._bounding_rect)

    def mergeWith(self, command: QUndoCommand) -> bool:
        if not isinstance(command, PaintStrokeCommand):
            return False
        paint_undo_command = cast(PaintStrokeCommand, command)

        if not paint_undo_command._mergeable:
            return False

        self._stroke_polygons = Polygon.union(self._stroke_polygons + paint_undo_command._stroke_polygons)
        self._calculateBoundingRect()

        return True

    def _clearTextureBits(self, painter: QPainter, extended = False):
        painter.setBrush(QBrush(self._getBitRangeMask()))
        painter.setPen(QPen(painter.brush(), self.PEN_OVERLAP_WIDTH_EXTENDED if extended else self.PEN_OVERLAP_WIDTH))
        painter.setCompositionMode(QPainter.CompositionMode.RasterOp_NotSourceAndDestination)
        painter.drawPath(self._makePainterPath())

    def _makePainterPath(self) -> QPainterPath:
        path = QPainterPath()
        for polygon in self._stroke_polygons:
            path.moveTo(polygon[0][0], polygon[0][1])
            for point in polygon:
                path.lineTo(point[0], point[1])
            path.closeSubpath()

        return path

    def _calculateBoundingRect(self):
        bounding_box = Polygon.getGlobalBoundingBox(self._stroke_polygons)
        if bounding_box is None:
            self._bounding_rect =  QRect()
        else:
            self._bounding_rect = QRect(
                QPoint(math.floor(bounding_box.left - PaintStrokeCommand.PEN_OVERLAP_WIDTH),
                       math.floor(bounding_box.bottom - PaintStrokeCommand.PEN_OVERLAP_WIDTH)),
                QPoint(math.ceil(bounding_box.right + PaintStrokeCommand.PEN_OVERLAP_WIDTH),
                       math.ceil(bounding_box.top + PaintStrokeCommand.PEN_OVERLAP_WIDTH)))
            self._bounding_rect &= self._texture.getImage().rect()