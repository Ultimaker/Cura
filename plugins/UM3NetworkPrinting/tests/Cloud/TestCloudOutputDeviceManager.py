# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from unittest import TestCase
from unittest.mock import patch

from cura.CuraApplication import CuraApplication
from plugins.UM3NetworkPrinting.src.Cloud.CloudOutputDevice import CloudOutputDevice
from plugins.UM3NetworkPrinting.src.Cloud.CloudOutputDeviceManager import CloudOutputDeviceManager
from plugins.UM3NetworkPrinting.tests.Cloud.NetworkManagerMock import NetworkManagerMock


@patch("cura.NetworkClient.QNetworkAccessManager")
class TestCloudOutputDeviceManager(TestCase):
    app = CuraApplication.getInstance() or CuraApplication()

    def setUp(self):
        super().setUp()
        self.app.initialize()

        self.network = NetworkManagerMock()
        self.network.prepareResponse(
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

    def tearDown(self):
        super().tearDown()

    def test_device(self, network_mock):
        network_mock.return_value = self.network

        manager = CloudOutputDeviceManager()
        manager._account.loginStateChanged.emit(True)
        manager._update_timer.timeout.emit()

        self.network.flushReplies()

        devices = self.app.getOutputDeviceManager().getOutputDevices()
        self.assertEqual([CloudOutputDevice], list(map(type, devices)))
