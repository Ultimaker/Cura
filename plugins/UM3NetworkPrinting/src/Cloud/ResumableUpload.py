# Copyright (c) 2018 Ultimaker B.V.
# !/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from typing import Optional, Callable, Any, Tuple

from UM.Logger import Logger
from cura.NetworkClient import NetworkClient


class ResumableUpload(NetworkClient):
    MAX_RETRIES = 10
    BYTES_PER_REQUEST = 256 * 1024
    RETRY_HTTP_CODES = {500, 502, 503, 504}

    ## Creates a resumable upload
    #  \param url: The URL to which we shall upload.
    #  \param content_length: The total content length of the file, in bytes.
    #  \param http_method: The HTTP method to be used, e.g. "POST" or "PUT".
    #  \param timeout: The timeout for each chunk upload. Important: If None, no timeout is applied at all.
    def __init__(self, url: str, content_type: str, data: bytes,
                 on_finished: Callable[[], Any], on_progress: Callable[[int], Any], on_error: Callable[[], Any]):
        super().__init__()
        self._url = url
        self._content_type = content_type
        self._data = data

        self._on_finished = on_finished
        self._on_progress = on_progress
        self._on_error = on_error

        self._sent_bytes = 0
        self._retries = 0
        self._finished = False

    ##  We override _createEmptyRequest in order to add the user credentials.
    #   \param url: The URL to request
    #   \param content_type: The type of the body contents.
    def _createEmptyRequest(self, path: str, content_type: Optional[str] = "application/json") -> QNetworkRequest:
        request = super()._createEmptyRequest(path, content_type = self._content_type)

        first_byte, last_byte = self._chunkRange()
        content_range = "bytes {}-{}/{}".format(first_byte, last_byte - 1, len(self._data))
        request.setRawHeader(b"Content-Range", content_range.encode())
        Logger.log("i", "Uploading %s to %s", content_range, self._url)

        return request

    def _chunkRange(self) -> Tuple[int, int]:
        last_byte = min(len(self._data), self._sent_bytes + self.BYTES_PER_REQUEST)
        return self._sent_bytes, last_byte

    def start(self) -> None:
        super().start()
        if self._finished:
            self._sent_bytes = 0
            self._retries = 0
            self._finished = False
        self._uploadChunk()

    def stop(self):
        super().stop()
        Logger.log("i", "Stopped uploading")
        self._finished = True

    def _uploadChunk(self) -> None:
        if self._finished:
            raise ValueError("The upload is already finished")

        first_byte, last_byte = self._chunkRange()
        # self.put(self._url, data = self._data[first_byte:last_byte], content_type = self._content_type,
        #          on_finished = self.finishedCallback, on_progress = self._progressCallback)
        request = self._createEmptyRequest(self._url, content_type=self._content_type)

        reply = self._manager.put(request, self._data[first_byte:last_byte])
        reply.finished.connect(lambda: self._finishedCallback(reply))
        reply.uploadProgress.connect(self._progressCallback)
        reply.error.connect(self._errorCallback)
        if reply.isFinished():
            self._finishedCallback(reply)

    def _progressCallback(self, bytes_sent: int, bytes_total: int) -> None:
        Logger.log("i", "Progress callback %s / %s", bytes_sent, bytes_total)
        if bytes_total:
            self._on_progress(int((self._sent_bytes + bytes_sent) / len(self._data) * 100))

    def _errorCallback(self, reply: QNetworkReply) -> None:
        body = bytes(reply.readAll()).decode()
        Logger.log("e", "Received error while uploading: %s", body)
        self.stop()
        self._on_error()

    def _finishedCallback(self, reply: QNetworkReply) -> None:
        Logger.log("i", "Finished callback %s %s",
                   reply.attribute(QNetworkRequest.HttpStatusCodeAttribute), reply.url().toString())

        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)

        if self._retries < self.MAX_RETRIES and status_code in self.RETRY_HTTP_CODES:
            self._retries += 1
            Logger.log("i", "Retrying %s/%s request %s", self._retries, self.MAX_RETRIES, reply.url().toString())
            self._uploadChunk()
            return

        if status_code > 308:
            self._errorCallback(reply)
            return

        body = bytes(reply.readAll()).decode()
        Logger.log("w", "status_code: %s, Headers: %s, body: %s", status_code,
                   [bytes(header).decode() for header in reply.rawHeaderList()], body)

        first_byte, last_byte = self._chunkRange()
        self._sent_bytes += last_byte - first_byte
        if self._sent_bytes >= len(self._data):
            self.stop()
            self._on_finished()
        else:
            self._uploadChunk()
