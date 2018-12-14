# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from time import time
from typing import Optional, Dict, Callable, List, Union

from PyQt5.QtCore import QUrl, QObject
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply, QHttpMultiPart, QNetworkRequest, QHttpPart, \
    QAuthenticator

from UM.Application import Application
from UM.Logger import Logger


##  Abstraction of QNetworkAccessManager for easier networking in Cura.
#   This was originally part of NetworkedPrinterOutputDevice but was moved out for re-use in other classes.
class NetworkClient(QObject):
    
    def __init__(self) -> None:
        super().__init__()

        # Network manager instance to use for this client.
        self._manager = None  # type: Optional[QNetworkAccessManager]

        # Timings.
        self._last_manager_create_time = None  # type: Optional[float]
        self._last_response_time = None  # type: Optional[float]
        self._last_request_time = None  # type: Optional[float]

        # The user agent of Cura.
        application = Application.getInstance()
        self._user_agent = "%s/%s " % (application.getApplicationName(), application.getVersion())

        # QHttpMultiPart objects need to be kept alive and not garbage collected during the
        # HTTP which uses them. We hold references to these QHttpMultiPart objects here.
        self._kept_alive_multiparts = {}  # type: Dict[QNetworkReply, QHttpMultiPart]

    ##  Creates a network manager if needed, with all the required properties and event bindings.
    def start(self) -> None:
        if self._manager:
            return
        self._manager = QNetworkAccessManager()
        self._last_manager_create_time = time()
        self._manager.authenticationRequired.connect(self._onAuthenticationRequired)

    ##  Destroys the network manager and event bindings.
    def stop(self) -> None:
        if not self._manager:
            return
        self._manager.authenticationRequired.disconnect(self._onAuthenticationRequired)
        self._manager = None

    ##  Create a new empty network request.
    #   Automatically adds the required HTTP headers.
    #   \param url: The URL to request
    #   \param content_type: The type of the body contents.
    def _createEmptyRequest(self, url: str, content_type: Optional[str] = "application/json") -> QNetworkRequest:
        if not self._manager:
            self.start()  # make sure the manager is created
        request = QNetworkRequest(QUrl(url))
        if content_type:
            request.setHeader(QNetworkRequest.ContentTypeHeader, content_type)
        request.setHeader(QNetworkRequest.UserAgentHeader, self._user_agent)
        self._last_request_time = time()
        return request

    ##  Removes all cached Multi-Part items.
    def _clearCachedMultiPart(self, reply: QNetworkReply) -> None:
        if reply in self._kept_alive_multiparts:
            del self._kept_alive_multiparts[reply]

    ##  Callback for when the network manager detects that authentication is required but was not given.
    @staticmethod
    def _onAuthenticationRequired(reply: QNetworkReply, authenticator: QAuthenticator) -> None:
        Logger.log("w", "Request to {} required authentication but was not given".format(reply.url().toString()))

    ##  Add a part to a Multi-Part form.
    @staticmethod
    def _createFormPart(content_header: str, data: bytes, content_type: Optional[str] = None) -> QHttpPart:
        part = QHttpPart()

        if not content_header.startswith("form-data;"):
            content_header = "form_data; " + content_header

        part.setHeader(QNetworkRequest.ContentDispositionHeader, content_header)

        if content_type is not None:
            part.setHeader(QNetworkRequest.ContentTypeHeader, content_type)

        part.setBody(data)
        return part

    ##  Public version of _createFormPart. Both are needed for backward compatibility with 3rd party plugins.
    def createFormPart(self, content_header: str, data: bytes, content_type: Optional[str] = None) -> QHttpPart:
        return self._createFormPart(content_header, data, content_type)

    ## Sends a put request to the given path.
    #  url: The path after the API prefix.
    #  data: The data to be sent in the body
    #  content_type: The content type of the body data.
    #  on_finished: The function to call when the response is received.
    #  on_progress: The function to call when the progress changes. Parameters are bytes_sent / bytes_total.
    def put(self, url: str, data: Union[str, bytes], content_type: Optional[str] = None,
            on_finished: Optional[Callable[[QNetworkReply], None]] = None,
            on_progress: Optional[Callable[[int, int], None]] = None) -> None:
        request = self._createEmptyRequest(url, content_type = content_type)

        body = data if isinstance(data, bytes) else data.encode()  # type: bytes
        reply = self._manager.put(request, body)
        callback = self._createCallback(reply, on_finished)
        reply.finished.connect(callback)
        if on_progress is not None:
            reply.uploadProgress.connect(on_progress)

    ## Sends a delete request to the given path.
    #  url: The path after the API prefix.
    #  on_finished: The function to be call when the response is received.
    def delete(self, url: str, on_finished: Optional[Callable[[QNetworkReply], None]]) -> None:
        request = self._createEmptyRequest(url)
        reply = self._manager.deleteResource(request)
        callback = self._createCallback(reply, on_finished)
        reply.finished.connect(callback)

    ## Sends a get request to the given path.
    #  \param url: The path after the API prefix.
    #  \param on_finished: The function to be call when the response is received.
    def get(self, url: str, on_finished: Optional[Callable[[QNetworkReply], None]]) -> None:
        request = self._createEmptyRequest(url)
        reply = self._manager.get(request)
        callback = self._createCallback(reply, on_finished)
        reply.finished.connect(callback)

    ## Sends a post request to the given path.
    #  \param url: The path after the API prefix.
    #  \param data: The data to be sent in the body
    #  \param on_finished: The function to call when the response is received.
    #  \param on_progress: The function to call when the progress changes. Parameters are bytes_sent / bytes_total.
    def post(self, url: str, data: Union[str, bytes],
             on_finished: Optional[Callable[[QNetworkReply], None]],
             on_progress: Optional[Callable[[int, int], None]] = None) -> None:
        request = self._createEmptyRequest(url)

        body = data if isinstance(data, bytes) else data.encode()  # type: bytes
        reply = self._manager.post(request, body)
        callback = self._createCallback(reply, on_finished)
        reply.finished.connect(callback)
        if on_progress is not None:
            reply.uploadProgress.connect(on_progress)

    ##  Does a POST request with form data to the given URL.
    def postForm(self, url: str, header_data: str, body_data: bytes,
                 on_finished: Optional[Callable[[QNetworkReply], None]],
                 on_progress: Optional[Callable[[int, int], None]] = None) -> None:
        post_part = QHttpPart()
        post_part.setHeader(QNetworkRequest.ContentDispositionHeader, header_data)
        post_part.setBody(body_data)
        self.postFormWithParts(url, [post_part], on_finished, on_progress)

    ##  Does a POST request with form parts to the given URL.
    def postFormWithParts(self, target: str, parts: List[QHttpPart],
                          on_finished: Optional[Callable[[QNetworkReply], None]],
                          on_progress: Optional[Callable[[int, int], None]] = None) -> Optional[QNetworkReply]:
        request = self._createEmptyRequest(target, content_type = None)
        multi_post_part = QHttpMultiPart(QHttpMultiPart.FormDataType)
        
        for part in parts:
            multi_post_part.append(part)

        reply = self._manager.post(request, multi_post_part)

        def callback():
            on_finished(reply)
            self._clearCachedMultiPart(reply)

        reply.finished.connect(callback)

        self._kept_alive_multiparts[reply] = multi_post_part

        if on_progress is not None:
            reply.uploadProgress.connect(on_progress)
            
        return reply

    @staticmethod
    def _createCallback(reply: QNetworkReply, on_finished: Optional[Callable[[QNetworkReply], None]] = None):
        return lambda: on_finished(reply)
