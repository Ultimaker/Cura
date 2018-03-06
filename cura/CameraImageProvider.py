from PyQt5.QtGui import QImage
from PyQt5.QtQuick import QQuickImageProvider
from PyQt5.QtCore import QSize

from UM.Application import Application

class CameraImageProvider(QQuickImageProvider):
    def __init__(self):
        QQuickImageProvider.__init__(self, QQuickImageProvider.Image)

    ##  Request a new image.
    def requestImage(self, id, size):
        for output_device in Application.getInstance().getOutputDeviceManager().getOutputDevices():
            try:
                return output_device.activePrinter.camera.getImage(), QSize(15, 15)
            except AttributeError:
                pass
        return QImage(), QSize(15, 15)