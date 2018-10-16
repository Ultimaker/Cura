# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtGui import QImage
from PyQt5.QtQuick import QQuickImageProvider
from PyQt5.QtCore import QSize

from UM.Application import Application

##  Creates screenshots of the current scene.
class CameraImageProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.Image)

    ##  Request a new image.
    #
    #   The image will be taken using the current camera position.
    #   Only the actual objects in the scene will get rendered. Not the build
    #   plate and such!
    #   \param id The ID for the image to create. This is the requested image
    #   source, with the "image:" scheme and provider identifier removed. It's
    #   a Qt thing, they'll provide this parameter.
    #   \param size The dimensions of the image to scale to.
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
