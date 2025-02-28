# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt6.QtGui import QImage
from PyQt6.QtQuick import QQuickImageProvider
from PyQt6.QtCore import QSize

from UM.Application import Application
from typing import Tuple


class PrintJobPreviewImageProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image)

    def requestImage(self, id: str, size: QSize) -> Tuple[QImage, QSize]:
        """Request a new image.

        :param id: id of the requested image
        :param size: is not used defaults to QSize(15, 15)
        :return: an tuple containing the image and size
        """

        # The id will have an uuid and an increment separated by a slash. As we don't care about the value of the
        # increment, we need to strip that first.
        uuid = id[id.find("/") + 1:]
        for output_device in Application.getInstance().getOutputDeviceManager().getOutputDevices():
            if not hasattr(output_device, "printJobs"):
                continue

            for print_job in output_device.printJobs:
                if print_job.key == uuid:
                    if print_job.getPreviewImage():
                        return print_job.getPreviewImage(), QSize(15, 15)

                    return QImage(), QSize(15, 15)
        return QImage(), QSize(15, 15)
