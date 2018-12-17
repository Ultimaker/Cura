# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from unittest import TestCase
from unittest.mock import patch

from cura.CuraApplication import CuraApplication
from src.Cloud.CloudOutputDevice import CloudOutputDevice
from src.Cloud.CloudOutputDeviceManager import CloudOutputDeviceManager
from tests.Cloud.Fixtures import parseFixture, readFixture
from .NetworkManagerMock import NetworkManagerMock


class TestCloudOutputDeviceManager(TestCase):
    maxDiff = None

    URL = "https://api-staging.ultimaker.com/connect/v1/clusters"

    def setUp(self):
        super().setUp()
        self.app = CuraApplication.getInstance()
        self.network = NetworkManagerMock()
        with patch("src.Cloud.CloudApiClient.QNetworkAccessManager", return_value = self.network):
            self.manager = CloudOutputDeviceManager()
        self.clusters_response = parseFixture("getClusters")
        self.network.prepareReply("GET", self.URL, 200, readFixture("getClusters"))

    def tearDown(self):
        try:
            self._beforeTearDown()
            self.manager.stop()
        finally:
            super().tearDown()

    ## Before tear down method we check whether the state of the output device manager is what we expect based on the
    #  mocked API response.
    def _beforeTearDown(self):
        # let the network send replies
        self.network.flushReplies()
        # get the created devices
        device_manager = self.app.getOutputDeviceManager()
        devices = device_manager.getOutputDevices()
        # get the server data
        clusters = self.clusters_response.get("data", [])
        self.assertEqual([CloudOutputDevice] * len(clusters), [type(d) for d in devices])
        self.assertEqual({cluster["cluster_id"] for cluster in clusters}, {device.key for device in devices})
        self.assertEqual(clusters, sorted((device.clusterData.toDict() for device in devices),
                                          key=lambda device_dict: device_dict["host_version"]))

        for device in clusters:
            device_manager.getOutputDevice(device["cluster_id"]).close()
            device_manager.removeOutputDevice(device["cluster_id"])

    ## Runs the initial request to retrieve the clusters.
    def _loadData(self):
        self.manager.start()
        self.manager._onLoginStateChanged(is_logged_in = True)
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

    @patch("cura.CuraApplication.CuraApplication.getGlobalContainerStack")
    def test_device_connects_by_cluster_id(self, global_container_stack_mock):
        active_machine_mock = global_container_stack_mock.return_value
        cluster1, cluster2 = self.clusters_response["data"]
        cluster_id = cluster1["cluster_id"]
        active_machine_mock.getMetaDataEntry.side_effect = {"um_cloud_cluster_id": cluster_id}.get

        self._loadData()

        self.assertTrue(self.app.getOutputDeviceManager().getOutputDevice(cluster1["cluster_id"]).isConnected())
        self.assertFalse(self.app.getOutputDeviceManager().getOutputDevice(cluster2["cluster_id"]).isConnected())
        self.assertEquals([], active_machine_mock.setMetaDataEntry.mock_calls)

    @patch("cura.CuraApplication.CuraApplication.getGlobalContainerStack")
    def test_device_connects_by_network_key(self, global_container_stack_mock):
        active_machine_mock = global_container_stack_mock.return_value

        cluster1, cluster2 = self.clusters_response["data"]
        network_key = cluster2["host_name"] + ".ultimaker.local"
        active_machine_mock.getMetaDataEntry.side_effect = {"um_network_key": network_key}.get

        self._loadData()

        self.assertFalse(self.app.getOutputDeviceManager().getOutputDevice(cluster1["cluster_id"]).isConnected())
        self.assertTrue(self.app.getOutputDeviceManager().getOutputDevice(cluster2["cluster_id"]).isConnected())

        active_machine_mock.setMetaDataEntry.assert_called_with("um_cloud_cluster_id", cluster2["cluster_id"])

    @patch("src.Cloud.CloudOutputDeviceManager.Message")
    def test_api_error(self, message_mock):
        self.clusters_response = {
            "errors": [{"id": "notFound", "title": "Not found!", "http_status": "404", "code": "notFound"}]
        }
        self.network.prepareReply("GET", self.URL, 200, self.clusters_response)
        self._loadData()
        message_mock.assert_called_once_with(text='Not found!', title='Error', lifetime=10, dismissable=True)
        message_mock.return_value.show.assert_called_once_with()
