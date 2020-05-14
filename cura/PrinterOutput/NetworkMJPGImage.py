# Copyright (c) 2018 Aldo Hoeben / fieldOfView
# NetworkMJPGImage is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import QUrl, pyqtProperty, pyqtSignal, pyqtSlot, QRect, QByteArray
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtQuick import QQuickPaintedItem
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkAccessManager

from UM.Logger import Logger

#
# A QQuickPaintedItem that progressively downloads a network mjpeg stream,
# picks it apart in individual jpeg frames, and paints it.
#
class NetworkMJPGImage(QQuickPaintedItem):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._stream_buffer = QByteArray()
        self._stream_buffer_start_index = -1
        self._network_manager = None  # type: QNetworkAccessManager
        self._image_request = None  # type: QNetworkRequest
        self._image_reply = None  # type: QNetworkReply
        self._image = QImage()
        self._image_rect = QRect()

        self._source_url = QUrl()
        self._started = False

        self._mirror = False

        self.setAntialiasing(True)

    ##  Ensure that close gets called when object is destroyed
    def __del__(self) -> None:
        self.stop()


    def paint(self, painter: "QPainter") -> None:
        if self._mirror:
            painter.drawImage(self.contentsBoundingRect(), self._image.mirrored())
            return

        painter.drawImage(self.contentsBoundingRect(), self._image)


    def setSourceURL(self, source_url: "QUrl") -> None:
        self._source_url = source_url
        self.sourceURLChanged.emit()
        if self._started:
            self.start()

    def getSourceURL(self) -> "QUrl":
        return self._source_url

    sourceURLChanged = pyqtSignal()
    source = pyqtProperty(QUrl, fget = getSourceURL, fset = setSourceURL, notify = sourceURLChanged)

    def setMirror(self, mirror: bool) -> None:
        if mirror == self._mirror:
            return
        self._mirror = mirror
        self.mirrorChanged.emit()
        self.update()

    def getMirror(self) -> bool:
        return self._mirror

    mirrorChanged = pyqtSignal()
    mirror = pyqtProperty(bool, fget = getMirror, fset = setMirror, notify = mirrorChanged)

    imageSizeChanged = pyqtSignal()

    @pyqtProperty(int, notify = imageSizeChanged)
    def imageWidth(self) -> int:
        return self._image.width()

    @pyqtProperty(int, notify = imageSizeChanged)
    def imageHeight(self) -> int:
        return self._image.height()


    @pyqtSlot()
    def start(self) -> None:
        self.stop()  # Ensure that previous requests (if any) are stopped.

        if not self._source_url:
            Logger.log("w", "Unable to start camera stream without target!")
            return
        self._started = True

        self._image_request = QNetworkRequest(self._source_url)
        if self._network_manager is None:
            self._network_manager = QNetworkAccessManager()

        self._image_reply = self._network_manager.get(self._image_request)
        self._image_reply.downloadProgress.connect(self._onStreamDownloadProgress)

    @pyqtSlot()
    def stop(self) -> None:
        self._stream_buffer = QByteArray()
        self._stream_buffer_start_index = -1

        if self._image_reply:
            try:
                try:
                    self._image_reply.downloadProgress.disconnect(self._onStreamDownloadProgress)
                except Exception:
                    pass

                if not self._image_reply.isFinished():
                    self._image_reply.close()
            except Exception:  # RuntimeError
                pass  # It can happen that the wrapped c++ object is already deleted.

            self._image_reply = None
            self._image_request = None

        self._network_manager = None

        self._started = False


    def _onStreamDownloadProgress(self, bytes_received: int, bytes_total: int) -> None:
        # An MJPG stream is (for our purpose) a stream of concatenated JPG images.
        # JPG images start with the marker 0xFFD8, and end with 0xFFD9
        if self._image_reply is None:
            return
        self._stream_buffer += self._image_reply.readAll()

        if len(self._stream_buffer) > 2000000:  # No single camera frame should be 2 Mb or larger
            Logger.log("w", "MJPEG buffer exceeds reasonable size. Restarting stream...")
            self.stop()  # resets stream buffer and start index
            self.start()
            return

        if self._stream_buffer_start_index == -1:
            self._stream_buffer_start_index = self._stream_buffer.indexOf(b'\xff\xd8')
        stream_buffer_end_index = self._stream_buffer.lastIndexOf(b'\xff\xd9')
        # If this happens to be more than a single frame, then so be it; the JPG decoder will
        # ignore the extra data. We do it like this in order not to get a buildup of frames

        if self._stream_buffer_start_index != -1 and stream_buffer_end_index != -1:
            jpg_data = self._stream_buffer[self._stream_buffer_start_index:stream_buffer_end_index + 2]
            self._stream_buffer = self._stream_buffer[stream_buffer_end_index + 2:]
            self._stream_buffer_start_index = -1
            self._image.loadFromData(jpg_data)

            if self._image.rect() != self._image_rect:
                self.imageSizeChanged.emit()

            self.update()
