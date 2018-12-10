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

    def setUp(self):
        super().setUp()
        self.app = CuraApplication.getInstance()
        if not self.app:
            self.app = CuraApplication()
            self.app.initialize()

        self.network = NetworkManagerMock()
        self.manager = CloudOutputDeviceManager()
        self.clusters_response = self.network.prepareGetClusters()

    ## In the tear down method we check whether the state of the output device manager is what we expect based on the
    #  mocked API response.
    def tearDown(self):
        super().tearDown()
        # let the network send replies
        self.network.flushReplies()
        # get the created devices
        devices = self.app.getOutputDeviceManager().getOutputDevices()
        # get the server data
        clusters = self.clusters_response["data"]
        self.assertEqual([CloudOutputDevice] * len(clusters), [type(d) for d in devices])
        self.assertEqual({cluster["cluster_id"] for cluster in clusters}, {device.key for device in devices})
        self.assertEqual({cluster["host_name"] for cluster in clusters}, {device.host_name for device in devices})

    ## Runs the initial request to retrieve the clusters.
    def _loadData(self, network_mock):
        network_mock.return_value = self.network
        self.manager._account.loginStateChanged.emit(True)
        self.manager._update_timer.timeout.emit()

    def test_device_is_created(self, network_mock):
        # just create the cluster, it is checked at tearDown
        self._loadData(network_mock)

    def test_device_is_updated(self, network_mock):
        self._loadData(network_mock)

        # update the cluster from member variable, which is checked at tearDown
        self.clusters_response["data"][0]["host_name"] = "New host name"
        self.network.prepareGetClusters(self.clusters_response)

        self.manager._update_timer.timeout.emit()

    def test_device_is_removed(self, network_mock):
        self._loadData(network_mock)

        # delete the cluster from member variable, which is checked at tearDown
        del self.clusters_response["data"][1]
        self.network.prepareGetClusters(self.clusters_response)

        self.manager._update_timer.timeout.emit()
