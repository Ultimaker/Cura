# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import json
import urllib.parse
from json import JSONDecodeError
from time import time
from typing import Callable, List, Type, TypeVar, Union, Optional, Tuple, Dict, Any, cast
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtNetwork import QNetworkRequest, QNetworkReply

from UM.Logger import Logger
from UM.TaskManagement.HttpRequestManager import HttpRequestManager
from UM.TaskManagement.HttpRequestScope import JsonDecoratorScope
from cura.API import Account
from cura.CuraApplication import CuraApplication
from cura.UltimakerCloud import UltimakerCloudConstants
from cura.UltimakerCloud.UltimakerCloudScope import UltimakerCloudScope
from .ToolPathUploader import ToolPathUploader
from ..Models.BaseModel import BaseModel
from ..Models.Http.CloudClusterWithConfigResponse import CloudClusterWithConfigResponse
from ..Models.Http.CloudClusterResponse import CloudClusterResponse
from ..Models.Http.CloudClusterStatus import CloudClusterStatus
from ..Models.Http.CloudError import CloudError
from ..Models.Http.CloudPrintJobResponse import CloudPrintJobResponse
from ..Models.Http.CloudPrintJobUploadRequest import CloudPrintJobUploadRequest
from ..Models.Http.CloudPrintResponse import CloudPrintResponse

CloudApiClientModel = TypeVar("CloudApiClientModel", bound=BaseModel)
"""The generic type variable used to document the methods below."""


class CloudApiClient:
    """The cloud API client is responsible for handling the requests and responses from the cloud.

    Each method should only handle models instead of exposing Any HTTP details.
    """

    # The cloud URL to use for this remote cluster.
    ROOT_PATH = UltimakerCloudConstants.CuraCloudAPIRoot
    CLUSTER_API_ROOT = f"{ROOT_PATH}/connect/v1"
    CURA_API_ROOT = f"{ROOT_PATH}/cura/v1"

    DEFAULT_REQUEST_TIMEOUT = 10  # seconds

    # In order to avoid garbage collection we keep the callbacks in this list.
    _anti_gc_callbacks = []  # type: List[Callable[[Any], None]]

    # Custom machine definition ID to cloud cluster name mapping
    _machine_id_to_name: Dict[str, str] = None

    def __init__(self, app: CuraApplication, on_error: Callable[[List[CloudError]], None]) -> None:
        """Initializes a new cloud API client.

        :param app:
        :param on_error: The callback to be called whenever we receive errors from the server.
        """
        super().__init__()
        self._app = app
        self._account = app.getCuraAPI().account
        self._scope = JsonDecoratorScope(UltimakerCloudScope(app))
        self._http = HttpRequestManager.getInstance()
        self._on_error = on_error
        self._upload: Optional[ToolPathUploader] = None

    @property
    def account(self) -> Account:
        """Gets the account used for the API."""
        return self._account

    def getClusters(self, on_finished: Callable[[List[CloudClusterResponse]], Any], failed: Callable) -> None:
        """Retrieves all the clusters for the user that is currently logged in.

        :param on_finished: The function to be called after the result is parsed.
        """

        url = f"{self.CLUSTER_API_ROOT}/clusters?status=active"
        self._http.get(url,
                       scope=self._scope,
                       callback=self._parseCallback(on_finished, CloudClusterResponse, failed),
                       error_callback=failed,
                       timeout=self.DEFAULT_REQUEST_TIMEOUT)

    def getClustersByMachineType(self, machine_type, on_finished: Callable[[List[CloudClusterWithConfigResponse]], Any], failed: Callable) -> None:
        # HACK: There is something weird going on with the API, as it reports printer types in formats like
        # "ultimaker_s3", but wants "Ultimaker S3" when using the machine_variant filter query. So we need to do some
        # conversion!
        # API points to "MakerBot Method" for a makerbot printertypes which we already changed to allign with other printer_type

        machine_id_to_name = self.getMachineIDMap()
        if machine_type in machine_id_to_name:
            machine_type = machine_id_to_name[machine_type]
        else:
            machine_type = machine_type.replace("_plus", "+")
            machine_type = machine_type.replace("_", " ")
            machine_type = machine_type.replace("ultimaker", "ultimaker ")
            machine_type = machine_type.replace("  ", " ")
            machine_type = machine_type.title()
            machine_type = urllib.parse.quote_plus(machine_type)
        url = f"{self.CLUSTER_API_ROOT}/clusters?machine_variant={machine_type}"
        self._http.get(url,
                       scope=self._scope,
                       callback=self._parseCallback(on_finished, CloudClusterWithConfigResponse, failed),
                       error_callback=failed,
                       timeout=self.DEFAULT_REQUEST_TIMEOUT)

    def getClusterStatus(self, cluster_id: str, on_finished: Callable[[CloudClusterStatus], Any]) -> None:
        """Retrieves the status of the given cluster.

        :param cluster_id: The ID of the cluster.
        :param on_finished: The function to be called after the result is parsed.
        """

        url = f"{self.CLUSTER_API_ROOT}/clusters/{cluster_id}/status"
        self._http.get(url,
                       scope=self._scope,
                       callback=self._parseCallback(on_finished, CloudClusterStatus),
                       timeout=self.DEFAULT_REQUEST_TIMEOUT)

    def requestUpload(self, request: CloudPrintJobUploadRequest,
                      on_finished: Callable[[CloudPrintJobResponse], Any]) -> None:

        """Requests the cloud to register the upload of a print job mesh.

        :param request: The request object.
        :param on_finished: The function to be called after the result is parsed.
        """

        url = f"{self.CURA_API_ROOT}/jobs/upload"
        data = json.dumps({"data": request.toDict()}).encode()

        self._http.put(url,
                       scope=self._scope,
                       data=data,
                       callback=self._parseCallback(on_finished, CloudPrintJobResponse),
                       timeout=self.DEFAULT_REQUEST_TIMEOUT)

    def uploadToolPath(self, print_job: CloudPrintJobResponse, mesh: bytes, on_finished: Callable[[], Any],
                       on_progress: Callable[[int], Any], on_error: Callable[[], Any]):
        """Uploads a print job tool path to the cloud.

        :param print_job: The object received after requesting an upload with `self.requestUpload`.
        :param mesh: The tool path data to be uploaded.
        :param on_finished: The function to be called after the upload is successful.
        :param on_progress: A function to be called during upload progress. It receives a percentage (0-100).
        :param on_error: A function to be called if the upload fails.
        """

        self._upload = ToolPathUploader(self._http, print_job, mesh, on_finished, on_progress, on_error)
        self._upload.start()

    # Requests a cluster to print the given print job.
    #  \param cluster_id: The ID of the cluster.
    #  \param job_id: The ID of the print job.
    #  \param on_finished: The function to be called after the result is parsed.
    #  \param on_error: A function to be called if there was a server-side problem uploading. Generic errors (not
    #  specific to sending print jobs) such as lost connection, unparsable responses, etc. are not returned here, but
    #  handled in a generic way by the CloudApiClient.
    def requestPrint(self, cluster_id: str, job_id: str, on_finished: Callable[[CloudPrintResponse], Any], on_error) -> None:
        url = f"{self.CLUSTER_API_ROOT}/clusters/{cluster_id}/print/{job_id}"
        self._http.post(url,
                        scope=self._scope,
                        data=b"",
                        callback=self._parseCallback(on_finished, CloudPrintResponse),
                        error_callback=on_error,
                        timeout=self.DEFAULT_REQUEST_TIMEOUT)

    def doPrintJobAction(self, cluster_id: str, cluster_job_id: str, action: str,
                         data: Optional[Dict[str, Any]] = None) -> None:

        """Send a print job action to the cluster for the given print job.

        :param cluster_id: The ID of the cluster.
        :param cluster_job_id: The ID of the print job within the cluster.
        :param action: The name of the action to execute.
        :param data: Optional data to send with the POST request
        """

        body = json.dumps({"data": data}).encode() if data else b""
        url = f"{self.CLUSTER_API_ROOT}/clusters/{cluster_id}/print_jobs/{cluster_job_id}/action/{action}"
        self._http.post(url,
                        scope=self._scope,
                        data=body,
                        timeout=self.DEFAULT_REQUEST_TIMEOUT)

    def _createEmptyRequest(self, path: str, content_type: Optional[str] = "application/json") -> QNetworkRequest:
        """We override _createEmptyRequest in order to add the user credentials.

        :param path: The URL to request
        :param content_type: The type of the body contents.
        """

        request = QNetworkRequest(QUrl(path))
        if content_type:
            request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, content_type)
        access_token = self._account.accessToken
        if access_token:
            request.setRawHeader(b"Authorization", f"Bearer {access_token}".encode())
        return request

    @staticmethod
    def _parseReply(reply: QNetworkReply) -> Tuple[int, Dict[str, Any]]:
        """Parses the given JSON network reply into a status code and a dictionary, handling unexpected errors as well.

        :param reply: The reply from the server.
        :return: A tuple with a status code and a dictionary.
        """

        status_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        try:
            response = bytes(reply.readAll()).decode()
            return status_code, json.loads(response)
        except (UnicodeDecodeError, JSONDecodeError, ValueError) as err:
            error = CloudError(code=type(err).__name__, title=str(err), http_code=str(status_code),
                               id=str(time()), http_status="500")
            Logger.logException("e", "Could not parse the stardust response: %s", error.toDict())
            return status_code, {"errors": [error.toDict()]}

    def _parseResponse(self,
                       response: Dict[str, Any],
                       on_finished: Union[Callable[[CloudApiClientModel], Any],
                                          Callable[[List[CloudApiClientModel]], Any]],
                       model_class: Type[CloudApiClientModel]) -> None:
        """Parses the given response and calls the correct callback depending on the result.

        :param response: The response from the server, after being converted to a dict.
        :param on_finished: The callback in case the response is successful.
        :param model_class: The type of the model to convert the response to. It may either be a single record or a list.
        """

        if "data" in response:
            data = response["data"]
            if "status" in data and data["status"] == "wait_approval":
                on_finished_empty = cast(Callable[[List], Any], on_finished)
                on_finished_empty([])
            elif isinstance(data, list):
                results = [model_class(**c) for c in data]  # type: List[CloudApiClientModel]
                on_finished_list = cast(Callable[[List[CloudApiClientModel]], Any], on_finished)
                on_finished_list(results)
            else:
                result = model_class(**data)  # type: CloudApiClientModel
                on_finished_item = cast(Callable[[CloudApiClientModel], Any], on_finished)
                on_finished_item(result)
        elif "errors" in response:
            self._on_error([CloudError(**error) for error in response["errors"]])
        else:
            Logger.log("e", "Cannot find data or errors in the cloud response: %s", response)

    def _parseCallback(self,
                       on_finished: Union[Callable[[CloudApiClientModel], Any],
                                          Callable[[List[CloudApiClientModel]], Any]],
                       model: Type[CloudApiClientModel],
                       on_error: Optional[Callable] = None) -> Callable[[QNetworkReply], None]:

        """Creates a callback function so that it includes the parsing of the response into the correct model.

        The callback is added to the 'finished' signal of the reply.
        :param reply: The reply that should be listened to.
        :param on_finished: The callback in case the response is successful. Depending on the endpoint it will be either
        a list or a single item.
        :param model: The type of the model to convert the response to.
        """

        def parse(reply: QNetworkReply) -> None:

            self._anti_gc_callbacks.remove(parse)

            # Don't try to parse the reply if we didn't get one
            if reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute) is None:
                if on_error is not None:
                    on_error()
                return

            status_code, response = self._parseReply(reply)
            if status_code >= 300 and on_error is not None:
                on_error()
            else:
                self._parseResponse(response, on_finished, model)

        self._anti_gc_callbacks.append(parse)
        return parse

    @classmethod
    def getMachineIDMap(cls) -> Dict[str, str]:
        if cls._machine_id_to_name is None:
            try:
                with open(Path(__file__).parent / "machine_id_to_name.json", "rt") as f:
                    cls._machine_id_to_name = json.load(f)
            except Exception as e:
                Logger.logException("e", f"Could not load machine_id_to_name.json: '{e}'")
                cls._machine_id_to_name = {}
        return cls._machine_id_to_name
