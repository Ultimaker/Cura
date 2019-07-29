# Copyright (c) 2018 Ultimaker B.V.
# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import List
from unittest import TestCase
from unittest.mock import patch, MagicMock

from cura.UltimakerCloudAuthentication import CuraCloudAPIRoot

from ...src.Cloud import CloudApiClient
from ...src.Models.Http.CloudClusterResponse import CloudClusterResponse
from ...src.Models.Http.CloudClusterStatus import CloudClusterStatus
from ...src.Models.Http.CloudPrintJobResponse import CloudPrintJobResponse
from ...src.Models.Http.CloudPrintJobUploadRequest import CloudPrintJobUploadRequest
from ...src.Models.Http.CloudError import CloudError

from .Fixtures import readFixture, parseFixture
from .NetworkManagerMock import NetworkManagerMock


class TestCloudApiClient(TestCase):
    maxDiff = None

    def _errorHandler(self, errors: List[CloudError]):
        raise Exception("Received unexpected error: {}".format(errors))

    def setUp(self):
        super().setUp()
        self.account = MagicMock()
        self.account.isLoggedIn.return_value = True

        self.network = NetworkManagerMock()
        with patch.object(CloudApiClient, 'QNetworkAccessManager', return_value = self.network):
            self.api = CloudApiClient.CloudApiClient(self.account, self._errorHandler)

    def test_getClusters(self):
        result = []

        response = readFixture("getClusters")
        data = parseFixture("getClusters")["data"]

        self.network.prepareReply("GET", CuraCloudAPIRoot + "/connect/v1/clusters", 200, response)
        # The callback is a function that adds the result of the call to getClusters to the result list
        self.api.getClusters(lambda clusters: result.extend(clusters))

        self.network.flushReplies()

        self.assertEqual([CloudClusterResponse(**data[0]), CloudClusterResponse(**data[1])], result)

    def test_getClusterStatus(self):
        result = []

        response = readFixture("getClusterStatusResponse")
        data = parseFixture("getClusterStatusResponse")["data"]

        url = CuraCloudAPIRoot + "/connect/v1/clusters/R0YcLJwar1ugh0ikEZsZs8NWKV6vJP_LdYsXgXqAcaNC/status"
        self.network.prepareReply("GET", url, 200, response)
        self.api.getClusterStatus("R0YcLJwar1ugh0ikEZsZs8NWKV6vJP_LdYsXgXqAcaNC", lambda s: result.append(s))

        self.network.flushReplies()

        self.assertEqual([CloudClusterStatus(**data)], result)

    def test_requestUpload(self):

        results = []

        response = readFixture("putJobUploadResponse")

        self.network.prepareReply("PUT", CuraCloudAPIRoot + "/cura/v1/jobs/upload", 200, response)
        request = CloudPrintJobUploadRequest(job_name = "job name", file_size = 143234, content_type = "text/plain")
        self.api.requestUpload(request, lambda r: results.append(r))
        self.network.flushReplies()

        self.assertEqual(["text/plain"], [r.content_type for r in results])
        self.assertEqual(["uploading"], [r.status for r in results])

    def test_uploadToolPath(self):

        results = []
        progress = MagicMock()

        data = parseFixture("putJobUploadResponse")["data"]
        upload_response = CloudPrintJobResponse(**data)

        # Network client doesn't look into the reply
        self.network.prepareReply("PUT", upload_response.upload_url, 200, b'{}')

        mesh = ("1234" * 100000).encode()
        self.api.uploadToolPath(upload_response, mesh, lambda: results.append("sent"), progress.advance, progress.error)

        for _ in range(10):
            self.network.flushReplies()
            self.network.prepareReply("PUT", upload_response.upload_url, 200, b'{}')

        self.assertEqual(["sent"], results)

    def test_requestPrint(self):

        results = []

        response = readFixture("postJobPrintResponse")

        cluster_id = "NWKV6vJP_LdYsXgXqAcaNCR0YcLJwar1ugh0ikEZsZs8"
        cluster_job_id = "9a59d8e9-91d3-4ff6-b4cb-9db91c4094dd"
        job_id = "ABCDefGHIjKlMNOpQrSTUvYxWZ0-1234567890abcDE="

        self.network.prepareReply("POST",
                                  CuraCloudAPIRoot + "/connect/v1/clusters/{}/print/{}"
                                  .format(cluster_id, job_id),
                                  200, response)

        self.api.requestPrint(cluster_id, job_id, lambda r: results.append(r))

        self.network.flushReplies()

        self.assertEqual([job_id], [r.job_id for r in results])
        self.assertEqual([cluster_job_id], [r.cluster_job_id for r in results])
        self.assertEqual(["queued"], [r.status for r in results])
