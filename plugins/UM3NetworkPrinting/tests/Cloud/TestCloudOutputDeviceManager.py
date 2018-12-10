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
        self.network.prepareGetClusters()

    def tearDown(self):
        super().tearDown()

    def test_device(self, network_mock):
        network_mock.return_value = self.network

        manager = CloudOutputDeviceManager()
        manager._account.loginStateChanged.emit(True)
        manager._update_timer.timeout.emit()

        self.network.flushReplies()

        devices = self.app.getOutputDeviceManager().getOutputDevices()
        self.assertEqual([CloudOutputDevice], [type(d) for d in devices])
        self.assertEqual(["R0YcLJwar1ugh0ikEZsZs8NWKV6vJP_LdYsXgXqAcaNC"], [d.key for d in devices])
        self.assertEqual(["ultimakersystem-ccbdd30044ec"], [d.host_name for d in devices])
