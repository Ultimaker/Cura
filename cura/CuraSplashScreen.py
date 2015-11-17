# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QColor, QFont
from PyQt5.QtWidgets import QSplashScreen

from UM.Resources import Resources
from UM.Application import Application

class CuraSplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        self.setPixmap(QPixmap(Resources.getPath(Resources.Images, "cura.png")))

    def drawContents(self, painter):
        painter.save()
        painter.setPen(QColor(0, 0, 0, 255))

        version = Application.getInstance().getVersion().split("-")

        painter.setFont(QFont("Roboto", 20))
        painter.drawText(0, 0, 203, 230, Qt.AlignRight | Qt.AlignBottom, version[0])
        painter.setFont(QFont("Roboto", 12))
        painter.drawText(0, 0, 203, 255, Qt.AlignRight | Qt.AlignBottom, version[1])

        painter.restore()
        super().drawContents(painter)
