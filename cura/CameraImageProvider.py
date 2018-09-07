from PyQt5.QtGui import QImage
from PyQt5.QtQuick import QQuickImageProvider
from PyQt5.QtCore import QSize

from UM.Application import Application


class CameraImageProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.Image)

    ##  Request a new image.
    def requestImage(self, id, size):
        for output_device in Application.getInstance().getOutputDeviceManager().getOutputDevices():
            try:
                image = output_device.activePrinter.camera.getImage()
                if image.isNull():
                    image = QImage()

                return image, QSize(15, 15)
            except AttributeError:
                try:
                    image = output_device.activeCamera.getImage()

                    return image, QSize(15, 15)
                except AttributeError:
                    pass

        return QImage(), QSize(15, 15)
