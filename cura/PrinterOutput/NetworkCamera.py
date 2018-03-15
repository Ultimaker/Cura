from UM.Logger import Logger

from PyQt5.QtCore import QUrl, pyqtProperty, pyqtSignal, QObject, pyqtSlot
from PyQt5.QtGui import QImage
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkAccessManager


class NetworkCamera(QObject):
    newImage = pyqtSignal()

    def __init__(self, target = None, parent = None):
        super().__init__(parent)
        self._stream_buffer = b""
        self._stream_buffer_start_index = -1
        self._manager = None
        self._image_request = None
        self._image_reply = None
        self._image = QImage()
        self._image_id = 0

        self._target = target
        self._started = False

    @pyqtSlot(str)
    def setTarget(self, target):
        restart_required = False
        if self._started:
            self.stop()
            restart_required = True

        self._target = target

        if restart_required:
            self.start()

    @pyqtProperty(QUrl, notify=newImage)
    def latestImage(self):
        self._image_id += 1
        # There is an image provider that is called "camera". In order to ensure that the image qml object, that
        # requires a QUrl to function, updates correctly we add an increasing number. This causes to see the QUrl
        # as new (instead of relying on cached version and thus forces an update.
        temp = "image://camera/" + str(self._image_id)

        return QUrl(temp, QUrl.TolerantMode)

    @pyqtSlot()
    def start(self):
        # Ensure that previous requests (if any) are stopped.
        self.stop()
        if self._target is None:
            Logger.log("w", "Unable to start camera stream without target!")
            return
        self._started = True
        url = QUrl(self._target)
        self._image_request = QNetworkRequest(url)
        if self._manager is None:
            self._manager = QNetworkAccessManager()

        self._image_reply = self._manager.get(self._image_request)
        self._image_reply.downloadProgress.connect(self._onStreamDownloadProgress)

    @pyqtSlot()
    def stop(self):
        self._stream_buffer = b""
        self._stream_buffer_start_index = -1

        if self._image_reply:
            try:
                # disconnect the signal
                try:
                    self._image_reply.downloadProgress.disconnect(self._onStreamDownloadProgress)
                except Exception:
                    pass
                # abort the request if it's not finished
                if not self._image_reply.isFinished():
                    self._image_reply.close()
            except Exception as e:  # RuntimeError
                pass  # It can happen that the wrapped c++ object is already deleted.

            self._image_reply = None
            self._image_request = None

        self._manager = None

        self._started = False

    def getImage(self):
        return self._image

    ##  Ensure that close gets called when object is destroyed
    def __del__(self):
        self.stop()

    def _onStreamDownloadProgress(self, bytes_received, bytes_total):
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

        self.newImage.emit()
