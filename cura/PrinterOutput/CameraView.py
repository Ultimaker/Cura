# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty, pyqtSignal
from PyQt5.QtGui import QImage
from PyQt5.QtQuick import QQuickPaintedItem


#
# A custom camera view that uses QQuickPaintedItem to present (or "paint") the image frames from a printer's
# network camera feed.
#
class CameraView(QQuickPaintedItem):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._image = QImage()

    imageChanged = pyqtSignal()

    def setImage(self, image: "QImage") -> None:
        self._image = image
        self.imageChanged.emit()
        self.update()

    def getImage(self) -> "QImage":
        return self._image

    image = pyqtProperty(QImage, fget = getImage, fset = setImage, notify = imageChanged)

    @pyqtProperty(int, notify = imageChanged)
    def imageWidth(self) -> int:
        return self._image.width()

    @pyqtProperty(int, notify = imageChanged)
    def imageHeight(self) -> int:
        return self._image.height()

    def paint(self, painter):
        painter.drawImage(self.contentsBoundingRect(), self._image)
