# Copyright (c) 2018 Ultimaker B.V.
# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import os
from typing import List
from unittest import TestCase
from unittest.mock import patch, MagicMock

from cura.CuraApplication import CuraApplication
from src.Cloud.CloudApiClient import CloudApiClient
from src.Cloud.Models.CloudPrintJobResponse import CloudPrintJobResponse
from src.Cloud.Models.CloudPrintJobUploadRequest import CloudPrintJobUploadRequest
from src.Cloud.Models.CloudErrorObject import CloudErrorObject
from tests.Cloud.Fixtures import readFixture, parseFixture
from .NetworkManagerMock import NetworkManagerMock


@patch("cura.NetworkClient.QNetworkAccessManager")
class TestCloudApiClient(TestCase):
    def _errorHandler(self, errors: List[CloudErrorObject]):
        raise Exception("Received unexpected error: {}".format(errors))

    def setUp(self):
        super().setUp()
        self.account = MagicMock()
        self.account.isLoggedIn.return_value = True

        self.app = CuraApplication.getInstance()
        self.network = NetworkManagerMock()
        self.api = CloudApiClient(self.account, self._errorHandler)

    def test_GetClusters(self, network_mock):
        network_mock.return_value = self.network

        result = []

        with open("{}/Fixtures/getClusters.json".format(os.path.dirname(__file__)), "rb") as f:
            response = f.read()

        self.network.prepareReply("GET", "https://api-staging.ultimaker.com/connect/v1/clusters", 200, response)
        # the callback is a function that adds the result of the call to getClusters to the result list
        self.api.getClusters(lambda clusters: result.extend(clusters))

        self.network.flushReplies()

        self.assertEqual(2, len(result))

    def test_getClusterStatus(self, network_mock):
        network_mock.return_value = self.network

        result = []

        with open("{}/Fixtures/getClusterStatusResponse.json".format(os.path.dirname(__file__)), "rb") as f:
            response = f.read()

        self.network.prepareReply("GET",
                                  "https://api-staging.ultimaker.com/connect/v1/clusters/R0YcLJwar1ugh0ikEZsZs8NWKV6vJP_LdYsXgXqAcaNC/status",
                                  200, response
                                  )
        self.api.getClusterStatus("R0YcLJwar1ugh0ikEZsZs8NWKV6vJP_LdYsXgXqAcaNC", lambda status: result.append(status))

        self.network.flushReplies()

        self.assertEqual(len(result), 1)
        status = result[0]

        self.assertEqual(len(status.printers), 2)
        self.assertEqual(len(status.print_jobs), 1)

    def test_requestUpload(self, network_mock):
        network_mock.return_value = self.network
        results = []

        response = readFixture("putJobUploadResponse")

        self.network.prepareReply("PUT", "https://api-staging.ultimaker.com/cura/v1/jobs/upload", 200, response)
        request = CloudPrintJobUploadRequest(job_name = "job name", file_size = 143234, content_type = "text/plain")
        self.api.requestUpload(request, lambda r: results.append(r))
        self.network.flushReplies()

        self.assertEqual(results[0].content_type, "text/plain")
        self.assertEqual(results[0].status, "uploading")

    def test_uploadMesh(self, network_mock):
        network_mock.return_value = self.network
        results = []
        progress = MagicMock()

        data = parseFixture("putJobUploadResponse")["data"]
        upload_response = CloudPrintJobResponse(**data)

        # Network client doesn't look into the reply
        self.network.prepareReply("PUT", upload_response.upload_url, 200, b'{}')

        mesh = ("1234" * 100000).encode()
        self.api.uploadMesh(upload_response, mesh, lambda: results.append("sent"), progress.advance, progress.error)

        for _ in range(10):
            self.network.flushReplies()
            self.network.prepareReply("PUT", upload_response.upload_url, 200, b'{}')

        self.assertEqual(["sent"], results)

    def test_requestPrint(self, network_mock):
        network_mock.return_value = self.network
        results = []

        response = readFixture("postJobPrintResponse")

        cluster_id = "NWKV6vJP_LdYsXgXqAcaNCR0YcLJwar1ugh0ikEZsZs8"
        cluster_job_id = "9a59d8e9-91d3-4ff6-b4cb-9db91c4094dd"
        job_id = "ABCDefGHIjKlMNOpQrSTUvYxWZ0-1234567890abcDE="

        self.network.prepareReply("POST",
                                  "https://api-staging.ultimaker.com/connect/v1/clusters/{}/print/{}"
                                  .format(cluster_id, job_id),
                                  200, response)

        self.api.requestPrint(cluster_id, job_id, lambda r: results.append(r))

        self.network.flushReplies()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].job_id, job_id)
        self.assertEqual(results[0].cluster_job_id, cluster_job_id)
        self.assertEqual(results[0].status, "queued")
