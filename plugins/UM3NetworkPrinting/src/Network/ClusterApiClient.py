# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Callable, List, Optional

from PyQt5.QtCore import QUrl
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply


## The ClusterApiClient is responsible for all network calls to local network clusters.
class ClusterApiClient:

    PRINTER_API_VERSION = "1"
    PRINTER_API_PREFIX = "/api/v" + PRINTER_API_VERSION

    CLUSTER_API_VERSION = "1"
    CLUSTER_API_PREFIX = "/cluster-api/v" + CLUSTER_API_VERSION

    ## Initializes a new cluster API client.
    #  \param address: The network address of the cluster to call.
    #  \param on_error: The callback to be called whenever we receive errors from the server.
    def __init__(self, address: str, on_error: Callable) -> None:
        super().__init__()
        self._manager = QNetworkAccessManager()
        self._address = address
        self._on_error = on_error
        self._upload = None  # type: # Optional[ToolPathUploader]
        # In order to avoid garbage collection we keep the callbacks in this list.
        self._anti_gc_callbacks = []  # type: List[Callable[[], None]]

    ## Get printer system information.
    #  \param on_finished: The callback in case the response is successful.
    def getSystem(self, on_finished: Callable) -> None:
        url = f"{self.PRINTER_API_PREFIX}/system"
        reply = self._manager.get(self._createEmptyRequest(url))
        self._addCallback(reply, on_finished)

    ## We override _createEmptyRequest in order to add the user credentials.
    #  \param url: The URL to request
    #  \param content_type: The type of the body contents.
    def _createEmptyRequest(self, path: str, content_type: Optional[str] = "application/json") -> QNetworkRequest:
        request = QNetworkRequest(QUrl(self._address + path))
        if content_type:
            request.setHeader(QNetworkRequest.ContentTypeHeader, content_type)
        return request

    ## Creates a callback function so that it includes the parsing of the response into the correct model.
    #  The callback is added to the 'finished' signal of the reply.
    #  \param reply: The reply that should be listened to.
    #  \param on_finished: The callback in case the response is successful.
    def _addCallback(self, reply: QNetworkReply, on_finished: Callable) -> None:
        def parse() -> None:
            # Don't try to parse the reply if we didn't get one
            if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) is None:
                return
            status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            response = bytes(reply.readAll()).decode()
            self._anti_gc_callbacks.remove(parse)
            on_finished(int(status_code), response)
            return
        self._anti_gc_callbacks.append(parse)
        reply.finished.connect(parse)
