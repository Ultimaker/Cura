from UM.Qt.Factory.QtGui import QImage
from UM.Qt.Factory.QtQuick import QQuickImageProvider
from UM.Qt.Factory.QtCore import QSize

from UM.Application import Application

class CameraImageProvider(QQuickImageProvider):
    def __init__(self):
        QQuickImageProvider.__init__(self, QQuickImageProvider.Image)

    ##  Request a new image.
    def requestImage(self, id, size):
        for output_device in Application.getInstance().getOutputDeviceManager().getOutputDevices():
            try:
                return output_device.getCameraImage(), QSize(15, 15)
            except AttributeError:
                pass
        return QImage(), QSize(15, 15)