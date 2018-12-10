# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import json
from unittest import TestCase
from unittest.mock import patch, MagicMock

from UM.Scene.SceneNode import SceneNode
from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel
from src.Cloud.CloudApiClient import CloudApiClient
from src.Cloud.CloudOutputDevice import CloudOutputDevice
from tests.Cloud.Fixtures import readFixture, parseFixture
from .NetworkManagerMock import NetworkManagerMock


@patch("cura.NetworkClient.QNetworkAccessManager")
class TestCloudOutputDevice(TestCase):
    CLUSTER_ID = "RIZ6cZbWA_Ua7RZVJhrdVfVpf0z-MqaSHQE4v8aRTtYq"
    JOB_ID = "ABCDefGHIjKlMNOpQrSTUvYxWZ0-1234567890abcDE="
    HOST_NAME = "ultimakersystem-ccbdd30044ec"

    BASE_URL = "https://api-staging.ultimaker.com"
    STATUS_URL = "{}/connect/v1/clusters/{}/status".format(BASE_URL, CLUSTER_ID)
    PRINT_URL = "{}/connect/v1/clusters/{}/print/{}".format(BASE_URL, CLUSTER_ID, JOB_ID)
    REQUEST_UPLOAD_URL = "{}/cura/v1/jobs/upload".format(BASE_URL)

    def setUp(self):
        super().setUp()
        self.app = CuraApplication.getInstance()
        self.network = NetworkManagerMock()
        self.account = MagicMock(isLoggedIn=True, accessToken="TestAccessToken")
        self.onError = MagicMock()
        self.device = CloudOutputDevice(CloudApiClient(self.account, self.onError), self.CLUSTER_ID, self.HOST_NAME)
        self.cluster_status = parseFixture("getClusterStatusResponse")
        self.network.prepareReply("GET", self.STATUS_URL, 200, readFixture("getClusterStatusResponse"))

    def tearDown(self):
        super().tearDown()
        self.network.flushReplies()

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

        self.assertEqual(["UM3PrintJobOutputModel"], [type(printer).__name__ for printer in self.device.printJobs])
        self.assertEqual({job["uuid"] for job in self.cluster_status["data"]["print_jobs"]},
                         {job.key for job in self.device.printJobs})
        self.assertEqual({job["owner"] for job in self.cluster_status["data"]["print_jobs"]},
                         {job.owner for job in self.device.printJobs})
        self.assertEqual({job["name"] for job in self.cluster_status["data"]["print_jobs"]},
                         {job.name for job in self.device.printJobs})

    def test_remove_print_job(self, network_mock):
        network_mock.return_value = self.network
        self.device._update()
        self.network.flushReplies()
        self.assertEqual(1, len(self.device.printJobs))

        self.cluster_status["data"]["print_jobs"].clear()
        self.network.prepareReply("GET", self.STATUS_URL, 200, self.cluster_status)
        self.device._update()
        self.network.flushReplies()
        self.assertEqual([], self.device.printJobs)

    def test_remove_printers(self, network_mock):
        network_mock.return_value = self.network
        self.device._update()
        self.network.flushReplies()
        self.assertEqual(2, len(self.device.printers))

        self.cluster_status["data"]["printers"].clear()
        self.network.prepareReply("GET", self.STATUS_URL, 200, self.cluster_status)
        self.device._update()
        self.network.flushReplies()
        self.assertEqual([], self.device.printers)

    @patch("cura.CuraApplication.CuraApplication.getGlobalContainerStack")
    def test_print_to_cloud(self, global_container_stack_mock, network_mock):
        active_machine_mock = global_container_stack_mock.return_value
        active_machine_mock.getMetaDataEntry.side_effect = {"file_formats": "application/gzip"}.get

        request_upload_response = parseFixture("putJobUploadResponse")
        request_print_response = parseFixture("postJobPrintResponse")
        self.network.prepareReply("PUT", self.REQUEST_UPLOAD_URL, 201, request_upload_response)
        self.network.prepareReply("PUT", request_upload_response["data"]["upload_url"], 201, b"{}")
        self.network.prepareReply("POST", self.PRINT_URL, 200, request_print_response)

        network_mock.return_value = self.network
        file_handler = MagicMock()
        file_handler.getSupportedFileTypesWrite.return_value = [{
            "extension": "gcode.gz",
            "mime_type": "application/gzip",
            "mode": 2, 
        }]
        file_handler.getWriterByMimeType.return_value.write.side_effect = \
            lambda stream, nodes: stream.write(str(nodes).encode())

        scene_nodes = [SceneNode()]
        self.device.requestWrite(scene_nodes, file_handler=file_handler, file_name="FileName")

        self.network.flushReplies()
        self.assertEqual({"data": {"content_type": "application/gzip", "file_size": 57, "job_name": "FileName"}},
                         json.loads(self.network.getRequestBody("PUT", self.REQUEST_UPLOAD_URL).decode()))
        self.assertEqual(str(scene_nodes).encode(),
                         self.network.getRequestBody("PUT", request_upload_response["data"]["upload_url"]))

        self.assertIsNone(self.network.getRequestBody("POST", self.PRINT_URL))
