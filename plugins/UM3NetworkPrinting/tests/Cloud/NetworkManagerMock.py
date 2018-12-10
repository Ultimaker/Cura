# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import json
from typing import Dict, Tuple, Union
from unittest.mock import MagicMock

from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply

from UM.Logger import Logger
from UM.Signal import Signal


## This class can be used to mock the QNetworkManager class and test the code using it.
#  After patching the QNetworkManager class, requests are prepared before they can be executed.
#  Any requests not prepared beforehand will cause KeyErrors.
class NetworkManagerMock:
    # signals used in the network manager.
    finished = Signal()
    authenticationRequired = Signal()

    # an enumeration of the supported operations and their code for the network access manager.
    _OPERATIONS = {
        "GET": QNetworkAccessManager.GetOperation,
        "POST": QNetworkAccessManager.PostOperation,
        "PUT": QNetworkAccessManager.PutOperation,
        "DELETE": QNetworkAccessManager.DeleteOperation,
        "HEAD": QNetworkAccessManager.HeadOperation,
    }

    ## Initializes the network manager mock.
    def __init__(self):
        # a dict with the prepared replies, using the format {(http_method, url): reply}
        self.replies = {}  # type: Dict[Tuple[str, str], QNetworkReply]

    ## Mock implementation  of the get, post, put, delete and head methods from the network manager.
    #  Since the methods are very simple and the same it didn't make sense to repeat the code.
    #  \param method: The method being called.
    #  \return The mocked function, if the method name is known. Defaults to the standard getattr function.
    def __getattr__(self, method: str):
        operation = self._OPERATIONS.get(method.upper())
        if operation:
            # this mock implementation will simply return the reply from the prepared ones.
            # it raises a KeyError if requests are done without being prepared.
            return lambda request, *_: self.replies[method.upper(), request.url().toString()]

        # the attribute is not one of the implemented methods, default to the standard implementation.
        return getattr(super(), method)

    ## Prepares a server reply for the given parameters.
    #  \param method: The HTTP method.
    #  \param url: The URL being requested.
    #  \param status_code: The HTTP status code for the response.
    #  \param response: The response body from the server (generally json-encoded).
    def prepareReply(self, method: str, url: str, status_code: int, response: Union[bytes, dict]) -> None:
        reply_mock = MagicMock()
        reply_mock.url().toString.return_value = url
        reply_mock.operation.return_value = self._OPERATIONS[method]
        reply_mock.attribute.return_value = status_code
        reply_mock.readAll.return_value = response if isinstance(response, bytes) else json.dumps(response).encode()
        self.replies[method, url] = reply_mock
        Logger.log("i", "Prepared mock {}-response to {} {}", status_code, method, url)

    ## Emits the signal that the reply is ready to all prepared replies.
    def flushReplies(self):
        for reply in self.replies.values():
            self.finished.emit(reply)
        self.reset()

    ## Deletes all prepared replies
    def reset(self):
        self.replies.clear()
