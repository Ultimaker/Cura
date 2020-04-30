# Copyright (c) 2019 Ultimaker B.V.
# !/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5.QtCore import QUrl
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkAccessManager
from typing import Optional, Callable, Any, Tuple, cast

from UM.Logger import Logger

from ..Models.Http.CloudPrintJobResponse import CloudPrintJobResponse


## Class responsible for uploading meshes to the cloud in separate requests.
class ToolPathUploader:

    # The maximum amount of times to retry if the server returns one of the RETRY_HTTP_CODES
    MAX_RETRIES = 10

    # The HTTP codes that should trigger a retry.
    RETRY_HTTP_CODES = {500, 502, 503, 504}

    # The amount of bytes to send per request
    BYTES_PER_REQUEST = 256 * 1024

    ## Creates a mesh upload object.
    #  \param manager: The network access manager that will handle the HTTP requests.
    #  \param print_job: The print job response that was returned by the cloud after registering the upload.
    #  \param data: The mesh bytes to be uploaded.
    #  \param on_finished: The method to be called when done.
    #  \param on_progress: The method to be called when the progress changes (receives a percentage 0-100).
    #  \param on_error: The method to be called when an error occurs.
    def __init__(self, manager: QNetworkAccessManager, print_job: CloudPrintJobResponse, data: bytes,
                 on_finished: Callable[[], Any], on_progress: Callable[[int], Any], on_error: Callable[[], Any]
                 ) -> None:
        self._manager = manager
        self._print_job = print_job
        self._data = data

        self._on_finished = on_finished
        self._on_progress = on_progress
        self._on_error = on_error

        self._sent_bytes = 0
        self._retries = 0
        self._finished = False
        self._reply = None  # type: Optional[QNetworkReply]

    ## Returns the print job for which this object was created.
    @property
    def printJob(self):
        return self._print_job

    ##  Creates a network request to the print job upload URL, adding the needed content range header.
    def _createRequest(self) -> QNetworkRequest:
        request = QNetworkRequest(QUrl(self._print_job.upload_url))
        request.setHeader(QNetworkRequest.ContentTypeHeader, self._print_job.content_type)

        first_byte, last_byte = self._chunkRange()
        content_range = "bytes {}-{}/{}".format(first_byte, last_byte - 1, len(self._data))
        request.setRawHeader(b"Content-Range", content_range.encode())
        Logger.log("i", "Uploading %s to %s", content_range, self._print_job.upload_url)

        return request

    ## Determines the bytes that should be uploaded next.
    #  \return: A tuple with the first and the last byte to upload.
    def _chunkRange(self) -> Tuple[int, int]:
        last_byte = min(len(self._data), self._sent_bytes + self.BYTES_PER_REQUEST)
        return self._sent_bytes, last_byte

    ## Starts uploading the mesh.
    def start(self) -> None:
        if self._finished:
            # reset state.
            self._sent_bytes = 0
            self._retries = 0
            self._finished = False
        self._uploadChunk()

    ## Stops uploading the mesh, marking it as finished.
    def stop(self):
        Logger.log("i", "Stopped uploading")
        self._finished = True

    ## Uploads a chunk of the mesh to the cloud.
    def _uploadChunk(self) -> None:
        if self._finished:
            raise ValueError("The upload is already finished")

        first_byte, last_byte = self._chunkRange()
        request = self._createRequest()

        # now send the reply and subscribe to the results
        self._reply = self._manager.put(request, self._data[first_byte:last_byte])
        self._reply.finished.connect(self._finishedCallback)
        self._reply.uploadProgress.connect(self._progressCallback)
        self._reply.error.connect(self._errorCallback)

    ## Handles an update to the upload progress
    #  \param bytes_sent: The amount of bytes sent in the current request.
    #  \param bytes_total: The amount of bytes to send in the current request.
    def _progressCallback(self, bytes_sent: int, bytes_total: int) -> None:
        Logger.log("i", "Progress callback %s / %s", bytes_sent, bytes_total)
        if bytes_total:
            total_sent = self._sent_bytes + bytes_sent
            self._on_progress(int(total_sent / len(self._data) * 100))

    ## Handles an error uploading.
    def _errorCallback(self) -> None:
        reply = cast(QNetworkReply, self._reply)
        body = bytes(reply.readAll()).decode()
        Logger.log("e", "Received error while uploading: %s", body)
        self.stop()
        self._on_error()

    ## Checks whether a chunk of data was uploaded successfully, starting the next chunk if needed.
    def _finishedCallback(self) -> None:
        reply = cast(QNetworkReply, self._reply)
        Logger.log("i", "Finished callback %s %s",
                   reply.attribute(QNetworkRequest.HttpStatusCodeAttribute), reply.url().toString())

        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)  # type: int

        # check if we should retry the last chunk
        if self._retries < self.MAX_RETRIES and status_code in self.RETRY_HTTP_CODES:
            self._retries += 1
            Logger.log("i", "Retrying %s/%s request %s", self._retries, self.MAX_RETRIES, reply.url().toString())
            try:
                self._uploadChunk()
            except ValueError:  # Asynchronously it could have completed in the meanwhile.
                pass
            return

        # Http codes that are not to be retried are assumed to be errors.
        if status_code > 308:
            self._errorCallback()
            return

        Logger.log("d", "status_code: %s, Headers: %s, body: %s", status_code,
                   [bytes(header).decode() for header in reply.rawHeaderList()], bytes(reply.readAll()).decode())
        self._chunkUploaded()

    ## Handles a chunk of data being uploaded, starting the next chunk if needed.
    def _chunkUploaded(self) -> None:
        # We got a successful response. Let's start the next chunk or report the upload is finished.
        first_byte, last_byte = self._chunkRange()
        self._sent_bytes += last_byte - first_byte
        if self._sent_bytes >= len(self._data):
            self.stop()
            self._on_finished()
        else:
            self._uploadChunk()
