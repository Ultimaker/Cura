# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import json
from typing import Dict, Tuple
from unittest.mock import MagicMock

from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply

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
    #  \param response: A dictionary with the response from the server (this is converted to JSON).
    def prepareReply(self, method: str, url: str, status_code: int, response: dict) -> None:
        reply_mock = MagicMock()
        reply_mock.url().toString.return_value = url
        reply_mock.operation.return_value = self._OPERATIONS[method]
        reply_mock.attribute.return_value = status_code
        reply_mock.readAll.return_value = json.dumps(response).encode()
        self.replies[method, url] = reply_mock

    ## Prepares a reply for the API call to get clusters.
    def prepareGetClusters(self) -> None:
        self.prepareReply(
            "GET", "https://api-staging.ultimaker.com/connect/v1/clusters",
            200, {
                "data": [{
                    "cluster_id": "RIZ6cZbWA_Ua7RZVJhrdVfVpf0z-MqaSHQE4v8aRTtYq",
                    "host_guid": "e90ae0ac-1257-4403-91ee-a44c9b7e8050",
                    "host_name": "ultimakersystem-ccbdd30044ec", "host_version": "5.1.2.20180807",
                    "is_online": False, "status": "inactive"
                }, {
                    "cluster_id": "R0YcLJwar1ugh0ikEZsZs8NWKV6vJP_LdYsXgXqAcaNC",
                    "host_guid": "e90ae0ac-1257-4403-91ee-a44c9b7e8050",
                    "host_name": "ultimakersystem-ccbdd30044ec", "host_version": "5.1.2.20180807",
                    "is_online": True, "status": "active"
                }]
            }
        )

    ## Emits the signal that the reply is ready to all prepared replies.
    def flushReplies(self):
        for reply in self.replies.values():
            self.finished.emit(reply)

    ## Deletes all prepared replies
    def reset(self):
        self.replies.clear()
