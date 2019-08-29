from PyQt5.QtGui import QImage
from PyQt5.QtQuick import QQuickImageProvider
from PyQt5.QtCore import QSize

from UM.Application import Application


class PrintJobPreviewImageProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.Image)

    ##  Request a new image.
    def requestImage(self, id: str, size: QSize) -> QImage:
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
                    else:
                        return QImage(), QSize(15, 15)
        return QImage(), QSize(15,15)