# Copyright (c) 2019 Ultimaker B.V.
# !/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from typing import Callable, Any, Tuple, cast, Dict, Optional

from UM.Logger import Logger
from UM.TaskManagement.HttpRequestManager import HttpRequestManager

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
    #  \param http: The HttpRequestManager that will handle the HTTP requests.
    #  \param print_job: The print job response that was returned by the cloud after registering the upload.
    #  \param data: The mesh bytes to be uploaded.
    #  \param on_finished: The method to be called when done.
    #  \param on_progress: The method to be called when the progress changes (receives a percentage 0-100).
    #  \param on_error: The method to be called when an error occurs.
    def __init__(self, http: HttpRequestManager, print_job: CloudPrintJobResponse, data: bytes,
                 on_finished: Callable[[], Any], on_progress: Callable[[int], Any], on_error: Callable[[], Any]
                 ) -> None:
        self._http = http
        self._print_job = print_job
        self._data = data

        self._on_finished = on_finished
        self._on_progress = on_progress
        self._on_error = on_error

        self._sent_bytes = 0
        self._retries = 0
        self._finished = False

    ## Returns the print job for which this object was created.
    @property
    def printJob(self):
        return self._print_job

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
        content_range = "bytes {}-{}/{}".format(first_byte, last_byte - 1, len(self._data))

        headers = {
            "Content-Type": cast(str, self._print_job.content_type),
            "Content-Range": content_range
        }  # type: Dict[str, str]

        Logger.log("i", "Uploading %s to %s", content_range, self._print_job.upload_url)

        self._http.put(
            url = cast(str, self._print_job.upload_url),
            headers_dict = headers,
            data = self._data[first_byte:last_byte],
            callback = self._finishedCallback,
            error_callback = self._errorCallback,
            upload_progress_callback = self._progressCallback
        )

    ## Handles an update to the upload progress
    #  \param bytes_sent: The amount of bytes sent in the current request.
    #  \param bytes_total: The amount of bytes to send in the current request.
    def _progressCallback(self, bytes_sent: int, bytes_total: int) -> None:
        Logger.log("i", "Progress callback %s / %s", bytes_sent, bytes_total)
        if bytes_total:
            total_sent = self._sent_bytes + bytes_sent
            self._on_progress(int(total_sent / len(self._data) * 100))

    ## Handles an error uploading.
    def _errorCallback(self, reply: QNetworkReply, error: QNetworkReply.NetworkError) -> None:
        body = bytes(reply.readAll()).decode()
        Logger.log("e", "Received error while uploading: %s", body)
        self.stop()
        self._on_error()

    ## Checks whether a chunk of data was uploaded successfully, starting the next chunk if needed.
    def _finishedCallback(self, reply: QNetworkReply) -> None:
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
            self._errorCallback(reply, None)
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
