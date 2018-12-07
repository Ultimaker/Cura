# Copyright (c) 2018 Ultimaker B.V.
# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import json
from typing import Dict, Tuple
from unittest import TestCase, mock
from unittest.mock import patch, MagicMock

from PyQt5.QtCore import QByteArray
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply

from UM.Application import Application
from UM.Signal import Signal
from cura.CuraApplication import CuraApplication
from plugins.UM3NetworkPrinting.src.Cloud.CloudApiClient import CloudApiClient
from plugins.UM3NetworkPrinting.src.Cloud.Models import CloudCluster, CloudErrorObject

# This mock application must extend from Application and not QtApplication otherwise some QObjects are created and
# a segfault is raised.
class FixtureApplication(Application):
    def __init__(self):
        super().__init__(name = "test", version = "1.0", api_version = "5.0.0")
        super().initialize()
        Signal._signalQueue = self

    def functionEvent(self, event):
        event.call()

    def parseCommandLine(self):
        pass

    def processEvents(self):
        pass

    def getRenderer(self):
        return MagicMock()

class ManagerMock:
    finished = Signal()
    authenticationRequired = Signal()

    def __init__(self, reply):
        self.reply = reply

    def get(self, request):
        self.reply.url.return_value = request.url()

        return self.reply

class ManagerMock2:
    finished = Signal()
    authenticationRequired = Signal()

    def get(self, request):
        reply_mock = MagicMock()
        reply_mock.url = request.url
        reply_mock.operation.return_value = QNetworkAccessManager.GetOperation
        return reply_mock

    @staticmethod
    def createReply(method: str, url: str, status_code: int, response: dict):
        reply_mock = MagicMock()
        reply_mock.url().toString.return_value = url
        reply_mock.operation.return_value = {
            "GET": QNetworkAccessManager.GetOperation,
            "POST": QNetworkAccessManager.PostOperation,
            "PUT": QNetworkAccessManager.PutOperation,
            "DELETE": QNetworkAccessManager.DeleteOperation,
            "HEAD": QNetworkAccessManager.HeadOperation,
        }[method]
        reply_mock.attribute.return_value = status_code
        reply_mock.readAll.return_value = json.dumps(response).encode()
        return reply_mock


class TestCloudApiClient(TestCase):

    app = CuraApplication.getInstance() or CuraApplication

    def _errorHandler(self, errors: [CloudErrorObject]):
        pass

    @patch("cura.NetworkClient.QNetworkAccessManager")
    @patch("cura.API.Account")
    def test_GetClusters(self, account_mock, manager_mock):
        reply_mock = MagicMock()
        reply_mock.operation.return_value = 2
        reply_mock.attribute.return_value = 200
        reply_mock.readAll.return_value = b'{"data": [{"cluster_id": "RIZ6cZbWA_Ua7RZVJhrdVfVpf0z-MqaSHQE4v8aRTtYq", "host_guid": "e90ae0ac-1257-4403-91ee-a44c9b7e8050", "host_name": "ultimakersystem-ccbdd30044ec", "host_version": "5.1.2.20180807", "is_online": false, "status": "inactive"}, {"cluster_id": "R0YcLJwar1ugh0ikEZsZs8NWKV6vJP_LdYsXgXqAcaNC", "host_guid": "e90ae0ac-1257-4403-91ee-a44c9b7e8050", "host_name": "ultimakersystem-ccbdd30044ec", "host_version": "5.1.2.20180807", "is_online": true, "status": "active"}]}'
        manager_mock.return_value = ManagerMock(reply_mock)
        account_mock.isLoggedIn.return_value = True

        result = []

        def _callback(clusters):
            result.extend(clusters)

        with mock.patch.object(Application, "getInstance", new = lambda: FixtureApplication()):
            api = CloudApiClient(account_mock, self._errorHandler)
            api.getClusters(_callback)

        manager_mock.return_value.finished.emit(reply_mock)

        self.assertEqual(2, len(result))

    @patch("cura.NetworkClient.QNetworkAccessManager")
    @patch("cura.API.Account")
    def test_GetClusters2(self, account_mock, manager_mock):
        manager = ManagerMock2()
        manager_mock.return_value = manager
        account_mock.isLoggedIn.return_value = True

        result = []

        # with mock.patch.object(Application, "getInstance", new = lambda: FixtureApplication()):
        api = CloudApiClient(account_mock, self._errorHandler)
        api.getClusters(lambda clusters: result.extend(clusters))

        manager.finished.emit(ManagerMock2.createReply(
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
        ))

        self.assertEqual(2, len(result))
