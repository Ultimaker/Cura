# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from unittest import TestCase
from unittest.mock import patch, MagicMock

from UM.OutputDevice.OutputDeviceManager import OutputDeviceManager
from cura.UltimakerCloudAuthentication import CuraCloudAPIRoot
from ...src.Cloud import CloudApiClient
from ...src.Cloud import CloudOutputDeviceManager
from .Fixtures import parseFixture, readFixture
from .NetworkManagerMock import NetworkManagerMock, FakeSignal


class TestCloudOutputDeviceManager(TestCase):
    maxDiff = None

    URL = CuraCloudAPIRoot + "/connect/v1/clusters"

    def setUp(self):
        super().setUp()
        self.app = MagicMock()
        self.device_manager = OutputDeviceManager()
        self.app.getOutputDeviceManager.return_value = self.device_manager

        self.patches = [patch("UM.Qt.QtApplication.QtApplication.getInstance", return_value=self.app),
                        patch("UM.Application.Application.getInstance", return_value=self.app)]
        for patched_method in self.patches:
            patched_method.start()

        self.network = NetworkManagerMock()
        self.timer = MagicMock(timeout = FakeSignal())
        with patch.object(CloudApiClient, "QNetworkAccessManager", return_value = self.network), \
                patch.object(CloudOutputDeviceManager, "QTimer", return_value = self.timer):
            self.manager = CloudOutputDeviceManager.CloudOutputDeviceManager()
        self.clusters_response = parseFixture("getClusters")
        self.network.prepareReply("GET", self.URL, 200, readFixture("getClusters"))

    def tearDown(self):
        try:
            self._beforeTearDown()

            self.network.flushReplies()
            self.manager.stop()
            for patched_method in self.patches:
                patched_method.stop()
        finally:
            super().tearDown()

    ## Before tear down method we check whether the state of the output device manager is what we expect based on the
    #  mocked API response.
    def _beforeTearDown(self):
        # let the network send replies
        self.network.flushReplies()
        # get the created devices
        devices = self.device_manager.getOutputDevices()
        # TODO: Check active device

        response_clusters = self.clusters_response.get("data", [])
        manager_clusters = sorted([device.clusterData.toDict() for device in self.manager._remote_clusters.values()],
                                  key=lambda cluster: cluster['cluster_id'], reverse=True)
        self.assertEqual(response_clusters, manager_clusters)

    ## Runs the initial request to retrieve the clusters.
    def _loadData(self):
        self.manager.start()
        self.network.flushReplies()

    def test_device_is_created(self):
        # just create the cluster, it is checked at tearDown
        self._loadData()

    def test_device_is_updated(self):
        self._loadData()

        # update the cluster from member variable, which is checked at tearDown
        self.clusters_response["data"][0]["host_name"] = "New host name"
        self.network.prepareReply("GET", self.URL, 200, self.clusters_response)

        self.manager._update_timer.timeout.emit()

    def test_device_is_removed(self):
        self._loadData()

        # delete the cluster from member variable, which is checked at tearDown
        del self.clusters_response["data"][1]
        self.network.prepareReply("GET", self.URL, 200, self.clusters_response)

        self.manager._update_timer.timeout.emit()

    def test_device_connects_by_cluster_id(self):
        active_machine_mock = self.app.getGlobalContainerStack.return_value
        cluster1, cluster2 = self.clusters_response["data"]
        cluster_id = cluster1["cluster_id"]
        active_machine_mock.getMetaDataEntry.side_effect = {"um_cloud_cluster_id": cluster_id}.get

        self._loadData()

        self.assertTrue(self.device_manager.getOutputDevice(cluster1["cluster_id"]).isConnected())
        self.assertIsNone(self.device_manager.getOutputDevice(cluster2["cluster_id"]))
        self.assertEquals([], active_machine_mock.setMetaDataEntry.mock_calls)

    def test_device_connects_by_network_key(self):
        active_machine_mock = self.app.getGlobalContainerStack.return_value

        cluster1, cluster2 = self.clusters_response["data"]
        network_key = cluster2["host_name"] + ".ultimaker.local"
        active_machine_mock.getMetaDataEntry.side_effect = {"um_network_key": network_key}.get

        self._loadData()

        self.assertIsNone(self.device_manager.getOutputDevice(cluster1["cluster_id"]))
        self.assertTrue(self.device_manager.getOutputDevice(cluster2["cluster_id"]).isConnected())

        active_machine_mock.setMetaDataEntry.assert_called_with("um_cloud_cluster_id", cluster2["cluster_id"])

    @patch.object(CloudOutputDeviceManager, "Message")
    def test_api_error(self, message_mock):
        self.clusters_response = {
            "errors": [{"id": "notFound", "title": "Not found!", "http_status": "404", "code": "notFound"}]
        }
        self.network.prepareReply("GET", self.URL, 200, self.clusters_response)
        self._loadData()
        message_mock.return_value.show.assert_called_once_with()
