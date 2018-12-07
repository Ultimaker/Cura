# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import json
from unittest.mock import MagicMock

from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

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

    def __getattr__(self, item):
        operation = self._OPERATIONS.get(item.upper())
        if operation:
            return lambda request, *_: self._fakeReply(operation, request)
        return super().__getattribute__(item)

    def _fakeReply(self, operation: QNetworkAccessManager.Operation, request: QNetworkRequest) -> QNetworkReply:
        reply_mock = MagicMock()
        reply_mock.url = request.url
        reply_mock.operation.return_value = operation
        return reply_mock

    def respond(self, method: str, url: str, status_code: int, response: dict) -> QNetworkReply:
        reply_mock = MagicMock()
        reply_mock.url().toString.return_value = url
        reply_mock.operation.return_value = self._OPERATIONS[method]
        reply_mock.attribute.return_value = status_code
        reply_mock.readAll.return_value = json.dumps(response).encode()
        self.finished.emit(reply_mock)
        return reply_mock
