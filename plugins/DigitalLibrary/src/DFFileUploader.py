# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt6.QtNetwork import QNetworkRequest, QNetworkReply
from typing import Callable, Any, cast, Optional, Union

from UM.Logger import Logger
from UM.TaskManagement.HttpRequestManager import HttpRequestManager
from .DFLibraryFileUploadResponse import DFLibraryFileUploadResponse
from .DFPrintJobUploadResponse import DFPrintJobUploadResponse


class DFFileUploader:
    """Class responsible for uploading meshes to the the digital factory library in separate requests."""

    # The maximum amount of times to retry if the server returns one of the RETRY_HTTP_CODES
    MAX_RETRIES = 10

    # The HTTP codes that should trigger a retry.
    RETRY_HTTP_CODES = {500, 502, 503, 504}

    def __init__(self,
                 http: HttpRequestManager,
                 df_file: Union[DFLibraryFileUploadResponse, DFPrintJobUploadResponse],
                 data: bytes,
                 on_finished: Callable[[str], Any],
                 on_success: Callable[[str], Any],
                 on_progress: Callable[[str, int], Any],
                 on_error: Callable[[str, "QNetworkReply", "QNetworkReply.NetworkError"], Any]
                 ) -> None:
        """Creates a mesh upload object.

        :param http: The network access manager that will handle the HTTP requests.
        :param df_file: The file response that was received by the Digital Factory after registering the upload.
        :param data: The mesh bytes to be uploaded.
        :param on_finished: The method to be called when done.
        :param on_success: The method to be called when the upload is successful.
        :param on_progress: The method to be called when the progress changes (receives a percentage 0-100).
        :param on_error: The method to be called when an error occurs.
        """

        self._http: HttpRequestManager = http
        self._df_file: Union[DFLibraryFileUploadResponse, DFPrintJobUploadResponse] = df_file
        self._file_name = ""
        if isinstance(self._df_file, DFLibraryFileUploadResponse):
            self._file_name = self._df_file.file_name
        elif isinstance(self._df_file, DFPrintJobUploadResponse):
            if self._df_file.job_name is not None:
                self._file_name = self._df_file.job_name
            else:
                self._file_name = ""
        else:
            raise TypeError("Incorrect input type")
        self._data: bytes = data

        self._on_finished = on_finished
        self._on_success = on_success
        self._on_progress = on_progress
        self._on_error = on_error

        self._retries = 0
        self._finished = False

    def start(self) -> None:
        """Starts uploading the mesh."""

        if self._finished:
            # reset state.
            self._retries = 0
            self._finished = False
        self._upload()

    def stop(self):
        """Stops uploading the mesh, marking it as finished."""

        Logger.log("i", "Finished uploading")
        self._finished = True  # Signal to any ongoing retries that we should stop retrying.
        self._on_finished(self._file_name)

    def _upload(self) -> None:
        """
        Uploads the file to the Digital Factory Library project
        """
        if self._finished:
            raise ValueError("The upload is already finished")
        if isinstance(self._df_file, DFLibraryFileUploadResponse):
            Logger.log("i", "Uploading Cura project file '{file_name}' via link '{upload_url}'".format(file_name = self._df_file.file_name, upload_url = self._df_file.upload_url))
        elif isinstance(self._df_file, DFPrintJobUploadResponse):
            Logger.log("i", "Uploading Cura print file '{file_name}' via link '{upload_url}'".format(file_name = self._df_file.job_name, upload_url = self._df_file.upload_url))
        self._http.put(
            url = cast(str, self._df_file.upload_url),
            headers_dict = {"Content-Type": cast(str, self._df_file.content_type)},
            data = self._data,
            callback = self._onUploadFinished,
            error_callback = self._onUploadError,
            upload_progress_callback = self._onUploadProgressChanged
        )

    def _onUploadProgressChanged(self, bytes_sent: int, bytes_total: int) -> None:
        """Handles an update to the upload progress

        :param bytes_sent: The amount of bytes sent in the current request.
        :param bytes_total: The amount of bytes to send in the current request.
        """
        Logger.debug("Cloud upload progress %s / %s", bytes_sent, bytes_total)
        if bytes_total:
            self._on_progress(self._file_name, int(bytes_sent / len(self._data) * 100))

    def _onUploadError(self, reply: QNetworkReply, error: QNetworkReply.NetworkError) -> None:
        """Handles an error uploading."""

        body = bytes(reply.peek(reply.bytesAvailable())).decode()
        Logger.log("e", "Received error while uploading: %s", body)
        self._on_error(self._file_name, reply, error)
        self.stop()

    def _onUploadFinished(self, reply: QNetworkReply) -> None:
        """
        Checks whether a chunk of data was uploaded successfully, starting the next chunk if needed.
        """

        Logger.log("i", "Finished callback %s %s",
                   reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute), reply.url().toString())

        status_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)  # type: Optional[int]
        if not status_code:
            Logger.log("e", "Reply contained no status code.")
            self._onUploadError(reply, None)
            return

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
            self._onUploadError(reply, None)
            return

        Logger.log("d", "status_code: %s, Headers: %s, body: %s", status_code,
                   [bytes(header).decode() for header in reply.rawHeaderList()], bytes(reply.readAll()).decode())
        self._on_success(self._file_name)
        self.stop()
