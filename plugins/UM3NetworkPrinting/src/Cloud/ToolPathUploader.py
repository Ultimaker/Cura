# Copyright (c) 2019 Ultimaker B.V.
# !/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from typing import Callable, Any, Tuple, cast, Dict, Optional

from UM.Logger import Logger
from UM.TaskManagement.HttpRequestManager import HttpRequestManager

from ..Models.Http.CloudPrintJobResponse import CloudPrintJobResponse


class ToolPathUploader:
    """Class responsible for uploading meshes to the cloud in separate requests."""


    # The maximum amount of times to retry if the server returns one of the RETRY_HTTP_CODES
    MAX_RETRIES = 10

    # The HTTP codes that should trigger a retry.
    RETRY_HTTP_CODES = {500, 502, 503, 504}

    def __init__(self, http: HttpRequestManager, print_job: CloudPrintJobResponse, data: bytes,
                 on_finished: Callable[[], Any], on_progress: Callable[[int], Any], on_error: Callable[[], Any]
                 ) -> None:
        """Creates a mesh upload object.

        :param manager: The network access manager that will handle the HTTP requests.
        :param print_job: The print job response that was returned by the cloud after registering the upload.
        :param data: The mesh bytes to be uploaded.
        :param on_finished: The method to be called when done.
        :param on_progress: The method to be called when the progress changes (receives a percentage 0-100).
        :param on_error: The method to be called when an error occurs.
        """

        self._http = http
        self._print_job = print_job
        self._data = data

        self._on_finished = on_finished
        self._on_progress = on_progress
        self._on_error = on_error

        self._retries = 0
        self._finished = False

    @property
    def printJob(self):
        """Returns the print job for which this object was created."""

        return self._print_job

    def start(self) -> None:
        """Starts uploading the mesh."""

        if self._finished:
            # reset state.
            self._retries = 0
            self._finished = False
        self._upload()

    def stop(self):
        """Stops uploading the mesh, marking it as finished."""

        Logger.log("i", "Stopped uploading")
        self._finished = True

    def _upload(self) -> None:
        """
        Uploads the print job to the cloud printer.
        """
        if self._finished:
            raise ValueError("The upload is already finished")

        Logger.log("i", "Uploading print to {upload_url}".format(upload_url = self._print_job.upload_url))
        self._http.put(
            url = cast(str, self._print_job.upload_url),
            headers_dict = {"Content-Type": cast(str, self._print_job.content_type)},
            data = self._data,
            callback = self._finishedCallback,
            error_callback = self._errorCallback,
            upload_progress_callback = self._progressCallback
        )

    def _progressCallback(self, bytes_sent: int, bytes_total: int) -> None:
        """Handles an update to the upload progress

        :param bytes_sent: The amount of bytes sent in the current request.
        :param bytes_total: The amount of bytes to send in the current request.
        """
        Logger.log("i", "Progress callback %s / %s", bytes_sent, bytes_total)
        if bytes_total:
            self._on_progress(int(bytes_sent / len(self._data) * 100))

    ## Handles an error uploading.
    def _errorCallback(self, reply: QNetworkReply, error: QNetworkReply.NetworkError) -> None:
        """Handles an error uploading."""

        body = bytes(reply.readAll()).decode()
        Logger.log("e", "Received error while uploading: %s", body)
        self.stop()
        self._on_error()

    def _finishedCallback(self, reply: QNetworkReply) -> None:
        """Checks whether a chunk of data was uploaded successfully, starting the next chunk if needed."""

        Logger.log("i", "Finished callback %s %s",
                   reply.attribute(QNetworkRequest.HttpStatusCodeAttribute), reply.url().toString())

        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)  # type: int

        # check if we should retry the last chunk
        if self._retries < self.MAX_RETRIES and status_code in self.RETRY_HTTP_CODES:
            self._retries += 1
            Logger.log("i", "Retrying %s/%s request %s", self._retries, self.MAX_RETRIES, reply.url().toString())
            try:
                self._upload()
            except ValueError:  # Asynchronously it could have completed in the meanwhile.
                pass
            return

        # Http codes that are not to be retried are assumed to be errors.
        if status_code > 308:
            self._errorCallback(reply, None)
            return

        Logger.log("d", "status_code: %s, Headers: %s, body: %s", status_code,
                   [bytes(header).decode() for header in reply.rawHeaderList()], bytes(reply.readAll()).decode())

        self.stop()
        self._on_finished()
