# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import json
from unittest import TestCase
from unittest.mock import patch, MagicMock

from UM.Scene.SceneNode import SceneNode
from cura.UltimakerCloudAuthentication import CuraCloudAPIRoot
from cura.PrinterOutput.Models.PrinterOutputModel import PrinterOutputModel
from ...src.Cloud import CloudApiClient
from ...src.Cloud.CloudOutputDevice import CloudOutputDevice
from ...src.Models.Http.CloudClusterResponse import CloudClusterResponse
from .Fixtures import readFixture, parseFixture
from .NetworkManagerMock import NetworkManagerMock


class TestCloudOutputDevice(TestCase):
    maxDiff = None

    CLUSTER_ID = "RIZ6cZbWA_Ua7RZVJhrdVfVpf0z-MqaSHQE4v8aRTtYq"
    JOB_ID = "ABCDefGHIjKlMNOpQrSTUvYxWZ0-1234567890abcDE="
    HOST_NAME = "ultimakersystem-ccbdd30044ec"
    HOST_GUID = "e90ae0ac-1257-4403-91ee-a44c9b7e8050"
    HOST_VERSION = "5.2.0"
    FRIENDLY_NAME = "My Friendly Printer"

    STATUS_URL = "{}/connect/v1/clusters/{}/status".format(CuraCloudAPIRoot, CLUSTER_ID)
    PRINT_URL = "{}/connect/v1/clusters/{}/print/{}".format(CuraCloudAPIRoot, CLUSTER_ID, JOB_ID)
    REQUEST_UPLOAD_URL = "{}/cura/v1/jobs/upload".format(CuraCloudAPIRoot)

    def setUp(self):
        super().setUp()
        self.app = MagicMock()

        self.patches = [patch("UM.Qt.QtApplication.QtApplication.getInstance", return_value=self.app),
                        patch("UM.Application.Application.getInstance", return_value=self.app)]
        for patched_method in self.patches:
            patched_method.start()

        self.cluster = CloudClusterResponse(self.CLUSTER_ID, self.HOST_GUID, self.HOST_NAME, is_online=True,
                                            status="active", host_version=self.HOST_VERSION,
                                            friendly_name=self.FRIENDLY_NAME)

        self.network = NetworkManagerMock()
        self.account = MagicMock(isLoggedIn=True, accessToken="TestAccessToken")
        self.onError = MagicMock()
        with patch.object(CloudApiClient, "QNetworkAccessManager", return_value = self.network):
            self._api = CloudApiClient.CloudApiClient(self.account, self.onError)

        self.device = CloudOutputDevice(self._api, self.cluster)
        self.cluster_status = parseFixture("getClusterStatusResponse")
        self.network.prepareReply("GET", self.STATUS_URL, 200, readFixture("getClusterStatusResponse"))

    def tearDown(self):
        try:
            super().tearDown()
            self.network.flushReplies()
        finally:
            for patched_method in self.patches:
                patched_method.stop()

    # We test for these in order to make sure the correct file type is selected depending on the firmware version.
    def test_properties(self):
        self.assertEqual(self.device.firmwareVersion, self.HOST_VERSION)
        self.assertEqual(self.device.name, self.FRIENDLY_NAME)

    def test_status(self):
        self.device._update()
        self.network.flushReplies()

        self.assertEqual([PrinterOutputModel, PrinterOutputModel], [type(printer) for printer in self.device.printers])

        controller_fields = {
            "_output_device": self.device,
            "can_abort": True,
            "can_control_manually": False,
            "can_pause": True,
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

    def test_remove_print_job(self):
        self.device._update()
        self.network.flushReplies()
        self.assertEqual(1, len(self.device.printJobs))

        self.cluster_status["data"]["print_jobs"].clear()
        self.network.prepareReply("GET", self.STATUS_URL, 200, self.cluster_status)

        self.device._last_request_time = None
        self.device._update()
        self.network.flushReplies()
        self.assertEqual([], self.device.printJobs)

    def test_remove_printers(self):
        self.device._update()
        self.network.flushReplies()
        self.assertEqual(2, len(self.device.printers))

        self.cluster_status["data"]["printers"].clear()
        self.network.prepareReply("GET", self.STATUS_URL, 200, self.cluster_status)

        self.device._last_request_time = None
        self.device._update()
        self.network.flushReplies()
        self.assertEqual([], self.device.printers)

    def test_print_to_cloud(self):
        active_machine_mock = self.app.getGlobalContainerStack.return_value
        active_machine_mock.getMetaDataEntry.side_effect = {"file_formats": "application/x-ufp"}.get

        request_upload_response = parseFixture("putJobUploadResponse")
        request_print_response = parseFixture("postJobPrintResponse")
        self.network.prepareReply("PUT", self.REQUEST_UPLOAD_URL, 201, request_upload_response)
        self.network.prepareReply("PUT", request_upload_response["data"]["upload_url"], 201, b"{}")
        self.network.prepareReply("POST", self.PRINT_URL, 200, request_print_response)

        file_handler = MagicMock()
        file_handler.getSupportedFileTypesWrite.return_value = [{
            "extension": "ufp",
            "mime_type": "application/x-ufp",
            "mode": 2
        }, {
            "extension": "gcode.gz",
            "mime_type": "application/gzip",
            "mode": 2,
        }]
        file_handler.getWriterByMimeType.return_value.write.side_effect = \
            lambda stream, nodes: stream.write(str(nodes).encode())

        scene_nodes = [SceneNode()]
        expected_mesh = str(scene_nodes).encode()
        self.device.requestWrite(scene_nodes, file_handler=file_handler, file_name="FileName")

        self.network.flushReplies()
        self.assertEqual(
            {"data": {"content_type": "application/x-ufp", "file_size": len(expected_mesh), "job_name": "FileName"}},
            json.loads(self.network.getRequestBody("PUT", self.REQUEST_UPLOAD_URL).decode())
        )
        self.assertEqual(expected_mesh,
                         self.network.getRequestBody("PUT", request_upload_response["data"]["upload_url"]))
        self.assertIsNone(self.network.getRequestBody("POST", self.PRINT_URL))
