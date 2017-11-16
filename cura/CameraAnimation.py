# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.


from PyQt5.QtCore import QVariantAnimation, QEasingCurve
from PyQt5.QtGui import QVector3D

from UM.Math.Vector import Vector


class CameraAnimation(QVariantAnimation):
    def __init__(self, parent = None):
        super().__init__(parent)
        self._camera_tool = None
        self.setDuration(300)
        self.setEasingCurve(QEasingCurve.OutQuad)

    def setCameraTool(self, camera_tool):
        self._camera_tool = camera_tool

    def setStart(self, start):
        self.setStartValue(QVector3D(start.x, start.y, start.z))

    def setTarget(self, target):
        self.setEndValue(QVector3D(target.x, target.y, target.z))

    def updateCurrentValue(self, value):
        self._camera_tool.setOrigin(Vector(value.x(), value.y(), value.z()))
