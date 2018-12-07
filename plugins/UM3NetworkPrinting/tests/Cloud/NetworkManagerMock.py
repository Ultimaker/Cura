# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import json
from typing import Dict, Tuple
from unittest.mock import MagicMock

from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply

from UM.Signal import Signal


class NetworkManagerMock:
    finished = Signal()
    authenticationRequired = Signal()

    _OPERATIONS = {
        "GET": QNetworkAccessManager.GetOperation,
        "POST": QNetworkAccessManager.PostOperation,
        "PUT": QNetworkAccessManager.PutOperation,
        "DELETE": QNetworkAccessManager.DeleteOperation,
        "HEAD": QNetworkAccessManager.HeadOperation,
    }

    def __init__(self):
        self.replies = {}  # type: Dict[Tuple[str, str], QNetworkReply]

    def __getattr__(self, method):
        operation = self._OPERATIONS.get(method.upper())
        if operation:
            return lambda request, *_: self.replies[method.upper(), request.url().toString()]
        return super().__getattribute__(method)

    def prepareResponse(self, method: str, url: str, status_code: int, response: dict) -> None:
        reply_mock = MagicMock()
        reply_mock.url().toString.return_value = url
        reply_mock.operation.return_value = self._OPERATIONS[method]
        reply_mock.attribute.return_value = status_code
        reply_mock.readAll.return_value = json.dumps(response).encode()
        self.replies[method, url] = reply_mock

    def flushReplies(self):
        for reply in self.replies.values():
            self.finished.emit(reply)

    def reset(self):
        self.replies.clear()
