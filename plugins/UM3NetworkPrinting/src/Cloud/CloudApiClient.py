# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import json
from json import JSONDecodeError
from time import time
from typing import Callable, List, Type, TypeVar, Union, Optional, Tuple, Dict, Any, cast

from PyQt5.QtCore import QUrl
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkAccessManager

from UM.Logger import Logger
from cura.API import Account
from cura.UltimakerCloud import UltimakerCloudAuthentication
from .ToolPathUploader import ToolPathUploader
from ..Models.BaseModel import BaseModel
from ..Models.Http.CloudClusterResponse import CloudClusterResponse
from ..Models.Http.CloudClusterStatus import CloudClusterStatus
from ..Models.Http.CloudError import CloudError
from ..Models.Http.CloudPrintJobResponse import CloudPrintJobResponse
from ..Models.Http.CloudPrintJobUploadRequest import CloudPrintJobUploadRequest
from ..Models.Http.CloudPrintResponse import CloudPrintResponse

## The generic type variable used to document the methods below.
CloudApiClientModel = TypeVar("CloudApiClientModel", bound=BaseModel)


## The cloud API client is responsible for handling the requests and responses from the cloud.
#  Each method should only handle models instead of exposing Any HTTP details.
class CloudApiClient:

    # The cloud URL to use for this remote cluster.
    ROOT_PATH = UltimakerCloudAuthentication.CuraCloudAPIRoot
    CLUSTER_API_ROOT = "{}/connect/v1".format(ROOT_PATH)
    CURA_API_ROOT = "{}/cura/v1".format(ROOT_PATH)

    # In order to avoid garbage collection we keep the callbacks in this list.
    _anti_gc_callbacks = []  # type: List[Callable[[], None]]

    ## Initializes a new cloud API client.
    #  \param account: The user's account object
    #  \param on_error: The callback to be called whenever we receive errors from the server.
    def __init__(self, account: Account, on_error: Callable[[List[CloudError]], None]) -> None:
        super().__init__()
        self._manager = QNetworkAccessManager()
        self._account = account
        self._on_error = on_error
        self._upload = None  # type: Optional[ToolPathUploader]

    ## Gets the account used for the API.
    @property
    def account(self) -> Account:
        return self._account

    ## Retrieves all the clusters for the user that is currently logged in.
    #  \param on_finished: The function to be called after the result is parsed.
    def getClusters(self, on_finished: Callable[[List[CloudClusterResponse]], Any]) -> None:
        url = "{}/clusters?status=active".format(self.CLUSTER_API_ROOT)
        reply = self._manager.get(self._createEmptyRequest(url))
        self._addCallback(reply, on_finished, CloudClusterResponse)

    ## Retrieves the status of the given cluster.
    #  \param cluster_id: The ID of the cluster.
    #  \param on_finished: The function to be called after the result is parsed.
    def getClusterStatus(self, cluster_id: str, on_finished: Callable[[CloudClusterStatus], Any]) -> None:
        url = "{}/clusters/{}/status".format(self.CLUSTER_API_ROOT, cluster_id)
        reply = self._manager.get(self._createEmptyRequest(url))
        self._addCallback(reply, on_finished, CloudClusterStatus)

    ## Requests the cloud to register the upload of a print job mesh.
    #  \param request: The request object.
    #  \param on_finished: The function to be called after the result is parsed.
    def requestUpload(self, request: CloudPrintJobUploadRequest,
                      on_finished: Callable[[CloudPrintJobResponse], Any]) -> None:
        url = "{}/jobs/upload".format(self.CURA_API_ROOT)
        body = json.dumps({"data": request.toDict()})
        reply = self._manager.put(self._createEmptyRequest(url), body.encode())
        self._addCallback(reply, on_finished, CloudPrintJobResponse)

    ## Uploads a print job tool path to the cloud.
    #  \param print_job: The object received after requesting an upload with `self.requestUpload`.
    #  \param mesh: The tool path data to be uploaded.
    #  \param on_finished: The function to be called after the upload is successful.
    #  \param on_progress: A function to be called during upload progress. It receives a percentage (0-100).
    #  \param on_error: A function to be called if the upload fails.
    def uploadToolPath(self, print_job: CloudPrintJobResponse, mesh: bytes, on_finished: Callable[[], Any],
                       on_progress: Callable[[int], Any], on_error: Callable[[], Any]):
        self._upload = ToolPathUploader(self._manager, print_job, mesh, on_finished, on_progress, on_error)
        self._upload.start()

    # Requests a cluster to print the given print job.
    #  \param cluster_id: The ID of the cluster.
    #  \param job_id: The ID of the print job.
    #  \param on_finished: The function to be called after the result is parsed.
    def requestPrint(self, cluster_id: str, job_id: str, on_finished: Callable[[CloudPrintResponse], Any]) -> None:
        url = "{}/clusters/{}/print/{}".format(self.CLUSTER_API_ROOT, cluster_id, job_id)
        reply = self._manager.post(self._createEmptyRequest(url), b"")
        self._addCallback(reply, on_finished, CloudPrintResponse)

    ##  Send a print job action to the cluster for the given print job.
    #  \param cluster_id: The ID of the cluster.
    #  \param cluster_job_id: The ID of the print job within the cluster.
    #  \param action: The name of the action to execute.
    def doPrintJobAction(self, cluster_id: str, cluster_job_id: str, action: str,
                         data: Optional[Dict[str, Any]] = None) -> None:
        body = json.dumps({"data": data}).encode() if data else b""
        url = "{}/clusters/{}/print_jobs/{}/action/{}".format(self.CLUSTER_API_ROOT, cluster_id, cluster_job_id, action)
        self._manager.post(self._createEmptyRequest(url), body)

    ##  We override _createEmptyRequest in order to add the user credentials.
    #   \param url: The URL to request
    #   \param content_type: The type of the body contents.
    def _createEmptyRequest(self, path: str, content_type: Optional[str] = "application/json") -> QNetworkRequest:
        request = QNetworkRequest(QUrl(path))
        if content_type:
            request.setHeader(QNetworkRequest.ContentTypeHeader, content_type)
        access_token = self._account.accessToken
        if access_token:
            request.setRawHeader(b"Authorization", "Bearer {}".format(access_token).encode())
        return request

    ## Parses the given JSON network reply into a status code and a dictionary, handling unexpected errors as well.
    #  \param reply: The reply from the server.
    #  \return A tuple with a status code and a dictionary.
    @staticmethod
    def _parseReply(reply: QNetworkReply) -> Tuple[int, Dict[str, Any]]:
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        try:
            response = bytes(reply.readAll()).decode()
            return status_code, json.loads(response)
        except (UnicodeDecodeError, JSONDecodeError, ValueError) as err:
            error = CloudError(code=type(err).__name__, title=str(err), http_code=str(status_code),
                               id=str(time()), http_status="500")
            Logger.logException("e", "Could not parse the stardust response: %s", error.toDict())
            return status_code, {"errors": [error.toDict()]}

    ## Parses the given models and calls the correct callback depending on the result.
    #  \param response: The response from the server, after being converted to a dict.
    #  \param on_finished: The callback in case the response is successful.
    #  \param model_class: The type of the model to convert the response to. It may either be a single record or a list.
    def _parseModels(self, response: Dict[str, Any],
                     on_finished: Union[Callable[[CloudApiClientModel], Any],
                                        Callable[[List[CloudApiClientModel]], Any]],
                     model_class: Type[CloudApiClientModel]) -> None:
        if "data" in response:
            data = response["data"]
            if isinstance(data, list):
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

    ## Creates a callback function so that it includes the parsing of the response into the correct model.
    #  The callback is added to the 'finished' signal of the reply.
    #  \param reply: The reply that should be listened to.
    #  \param on_finished: The callback in case the response is successful. Depending on the endpoint it will be either
    #       a list or a single item.
    #  \param model: The type of the model to convert the response to.
    def _addCallback(self,
                     reply: QNetworkReply,
                     on_finished: Union[Callable[[CloudApiClientModel], Any],
                                        Callable[[List[CloudApiClientModel]], Any]],
                     model: Type[CloudApiClientModel]) -> None:
        def parse() -> None:
            self._anti_gc_callbacks.remove(parse)

            # Don't try to parse the reply if we didn't get one
            if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) is None:
                return

            status_code, response = self._parseReply(reply)
            self._parseModels(response, on_finished, model)

        self._anti_gc_callbacks.append(parse)
        reply.finished.connect(parse)
