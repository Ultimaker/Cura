# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import json
import os
from unittest import TestCase
from unittest.mock import patch, MagicMock

from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel
from src.Cloud.CloudApiClient import CloudApiClient
from src.Cloud.CloudOutputController import CloudOutputController
from src.Cloud.CloudOutputDevice import CloudOutputDevice
from .NetworkManagerMock import NetworkManagerMock


@patch("cura.NetworkClient.QNetworkAccessManager")
class TestCloudOutputDevice(TestCase):
    CLUSTER_ID = "RIZ6cZbWA_Ua7RZVJhrdVfVpf0z-MqaSHQE4v8aRTtYq"
    HOST_NAME = "ultimakersystem-ccbdd30044ec"
    URL = "https://api-staging.ultimaker.com/connect/v1/clusters/{}/status".format(CLUSTER_ID)
    with open("{}/Fixtures/getClusterStatusResponse.json".format(os.path.dirname(__file__)), "rb") as f:
        DEFAULT_RESPONSE = f.read()

    def setUp(self):
        super().setUp()
        self.app = CuraApplication.getInstance()
        self.network = NetworkManagerMock()
        self.account = MagicMock(isLoggedIn=True, accessToken="TestAccessToken")
        self.onError = MagicMock()
        self.device = CloudOutputDevice(CloudApiClient(self.account, self.onError), self.CLUSTER_ID, self.HOST_NAME)
        self.cluster_status = json.loads(self.DEFAULT_RESPONSE.decode())
        self.network.prepareReply("GET", self.URL, 200, self.DEFAULT_RESPONSE)

    def tearDown(self):
        try:
            self._beforeTearDown()
        finally:
            super().tearDown()

    ## Before tear down method we check whether the state of the output device manager is what we expect based on the
    #  mocked API response.
    def _beforeTearDown(self):
        # let the network send replies
        self.network.flushReplies()
        # TODO

    def test_status(self, network_mock):
        network_mock.return_value = self.network
        self.device._update()
        self.network.flushReplies()

        self.assertEqual([PrinterOutputModel, PrinterOutputModel], [type(printer) for printer in self.device.printers])

        controller_fields = {
            "_output_device": self.device,
            "can_abort": False,
            "can_control_manually": False,
            "can_pause": False,
            "can_pre_heat_bed": False,
            "can_pre_heat_hotends": False,
            "can_send_raw_gcode": False,
            "can_update_firmware": False,
        }

        self.assertEqual({printer["uuid"] for printer in self.cluster_status["data"]["printers"]},
                         {printer.key for printer in self.device.printers})
        self.assertEqual([controller_fields, controller_fields],
                         [printer.getController().__dict__ for printer in self.device.printers])

        self.assertEqual({job["uuid"] for job in self.cluster_status["data"]["print_jobs"]},
                         {job.key for job in self.device.printJobs})
        self.assertEqual(["Daniel Testing"], [job.owner for job in self.device.printJobs])
        self.assertEqual(["UM3_dragon"], [job.name for job in self.device.printJobs])
