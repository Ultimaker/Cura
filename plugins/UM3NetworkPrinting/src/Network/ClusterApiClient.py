# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import json
from json import JSONDecodeError
from typing import Callable, List, Optional, Dict, Union, Any, Type, cast, TypeVar, Tuple

from PyQt6.QtCore import QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from UM.Logger import Logger

from ..Models.BaseModel import BaseModel
from ..Models.Http.ClusterPrintJobStatus import ClusterPrintJobStatus
from ..Models.Http.ClusterPrinterStatus import ClusterPrinterStatus
from ..Models.Http.PrinterSystemStatus import PrinterSystemStatus
from ..Models.Http.ClusterMaterial import ClusterMaterial


ClusterApiClientModel = TypeVar("ClusterApiClientModel", bound=BaseModel)
"""The generic type variable used to document the methods below."""


class ClusterApiClient:
    """The ClusterApiClient is responsible for all network calls to local network clusters."""


    PRINTER_API_PREFIX = "/api/v1"
    CLUSTER_API_PREFIX = "/cluster-api/v1"

    # In order to avoid garbage collection we keep the callbacks in this list.
    _anti_gc_callbacks = []  # type: List[Callable[[], None]]

    def __init__(self, address: str, on_error: Callable) -> None:
        """Initializes a new cluster API client.

        :param address: The network address of the cluster to call.
        :param on_error: The callback to be called whenever we receive errors from the server.
        """
        super().__init__()
        self._manager = QNetworkAccessManager()
        self._address = address
        self._on_error = on_error

    def getSystem(self, on_finished: Callable) -> None:
        """Get printer system information.

        :param on_finished: The callback in case the response is successful.
        """
        url = "{}/system".format(self.PRINTER_API_PREFIX)
        reply = self._manager.get(self._createEmptyRequest(url))
        self._addCallback(reply, on_finished, PrinterSystemStatus)

    def getMaterials(self, on_finished: Callable[[List[ClusterMaterial]], Any]) -> None:
        """Get the installed materials on the printer.

        :param on_finished: The callback in case the response is successful.
        """
        url = "{}/materials".format(self.CLUSTER_API_PREFIX)
        reply = self._manager.get(self._createEmptyRequest(url))
        self._addCallback(reply, on_finished, ClusterMaterial)

    def getPrinters(self, on_finished: Callable[[List[ClusterPrinterStatus]], Any]) -> None:
        """Get the printers in the cluster.

        :param on_finished: The callback in case the response is successful.
        """
        url = "{}/printers".format(self.CLUSTER_API_PREFIX)
        reply = self._manager.get(self._createEmptyRequest(url))
        self._addCallback(reply, on_finished, ClusterPrinterStatus)

    def getPrintJobs(self, on_finished: Callable[[List[ClusterPrintJobStatus]], Any]) -> None:
        """Get the print jobs in the cluster.

        :param on_finished: The callback in case the response is successful.
        """
        url = "{}/print_jobs".format(self.CLUSTER_API_PREFIX)
        reply = self._manager.get(self._createEmptyRequest(url))
        self._addCallback(reply, on_finished, ClusterPrintJobStatus)

    def movePrintJobToTop(self, print_job_uuid: str) -> None:
        """Move a print job to the top of the queue."""

        url = "{}/print_jobs/{}/action/move".format(self.CLUSTER_API_PREFIX, print_job_uuid)
        self._manager.post(self._createEmptyRequest(url), json.dumps({"to_position": 0, "list": "queued"}).encode())

    def forcePrintJob(self, print_job_uuid: str) -> None:
        """Override print job configuration and force it to be printed."""

        url = "{}/print_jobs/{}".format(self.CLUSTER_API_PREFIX, print_job_uuid)
        self._manager.put(self._createEmptyRequest(url), json.dumps({"force": True}).encode())

    def deletePrintJob(self, print_job_uuid: str) -> None:
        """Delete a print job from the queue."""

        url = "{}/print_jobs/{}".format(self.CLUSTER_API_PREFIX, print_job_uuid)
        self._manager.deleteResource(self._createEmptyRequest(url))

    def setPrintJobState(self, print_job_uuid: str, state: str) -> None:
        """Set the state of a print job."""

        url = "{}/print_jobs/{}/action".format(self.CLUSTER_API_PREFIX, print_job_uuid)
        # We rewrite 'resume' to 'print' here because we are using the old print job action endpoints.
        action = "print" if state == "resume" else state
        self._manager.put(self._createEmptyRequest(url), json.dumps({"action": action}).encode())

    def getPrintJobPreviewImage(self, print_job_uuid: str, on_finished: Callable) -> None:
        """Get the preview image data of a print job."""

        url = "{}/print_jobs/{}/preview_image".format(self.CLUSTER_API_PREFIX, print_job_uuid)
        reply = self._manager.get(self._createEmptyRequest(url))
        self._addCallback(reply, on_finished)

    def _createEmptyRequest(self, path: str, content_type: Optional[str] = "application/json") -> QNetworkRequest:
        """We override _createEmptyRequest in order to add the user credentials.

        :param url: The URL to request
        :param content_type: The type of the body contents.
        """
        url = QUrl("http://" + self._address + path)
        request = QNetworkRequest(url)
        if content_type:
            request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, content_type)
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
            Logger.logException("e", "Could not parse the cluster response: %s", err)
            return status_code, {"errors": [err]}

    def _parseModels(self, response: Dict[str, Any], on_finished: Union[Callable[[ClusterApiClientModel], Any],
                     Callable[[List[ClusterApiClientModel]], Any]], model_class: Type[ClusterApiClientModel]) -> None:
        """Parses the given models and calls the correct callback depending on the result.

        :param response: The response from the server, after being converted to a dict.
        :param on_finished: The callback in case the response is successful.
        :param model_class: The type of the model to convert the response to. It may either be a single record or a list.
        """

        try:
            if isinstance(response, list):
                results = [model_class(**c) for c in response]  # type: List[ClusterApiClientModel]
                on_finished_list = cast(Callable[[List[ClusterApiClientModel]], Any], on_finished)
                on_finished_list(results)
            else:
                result = model_class(**response)  # type: ClusterApiClientModel
                on_finished_item = cast(Callable[[ClusterApiClientModel], Any], on_finished)
                on_finished_item(result)
        except (JSONDecodeError, TypeError, ValueError):
            Logger.log("e", "Could not parse response from network: %s", str(response))

    def _addCallback(self, reply: QNetworkReply, on_finished: Union[Callable[[ClusterApiClientModel], Any],
                           Callable[[List[ClusterApiClientModel]], Any]], model: Type[ClusterApiClientModel] = None,
                     ) -> None:
        """Creates a callback function so that it includes the parsing of the response into the correct model.

        The callback is added to the 'finished' signal of the reply.
        :param reply: The reply that should be listened to.
        :param on_finished: The callback in case the response is successful.
        """

        def parse() -> None:
            try:
                self._anti_gc_callbacks.remove(parse)
            except ValueError:  # Already removed asynchronously.
                return  # Then the rest of the function is also already executed.

            # Don't try to parse the reply if we didn't get one
            if reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute) is None:
                return

            if reply.error() != QNetworkReply.NetworkError.NoError:
                self._on_error(reply.errorString())
                return

            # If no parse model is given, simply return the raw data in the callback.
            if not model:
                on_finished(reply.readAll())
                return

            # Otherwise parse the result and return the formatted data in the callback.
            status_code, response = self._parseReply(reply)
            self._parseModels(response, on_finished, model)

        self._anti_gc_callbacks.append(parse)
        reply.finished.connect(parse)
