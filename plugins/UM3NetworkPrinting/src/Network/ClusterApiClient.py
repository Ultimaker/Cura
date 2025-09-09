# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.
import hashlib
import json
import platform
import re
import secrets
from enum import StrEnum
from json import JSONDecodeError
from typing import Callable, List, Optional, Dict, Union, Any, Type, cast, TypeVar, Tuple

from PyQt6.QtCore import QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from UM.Logger import Logger

from cura.CuraApplication import CuraApplication

from ..Models.BaseModel import BaseModel
from ..Models.Http.ClusterPrintJobStatus import ClusterPrintJobStatus
from ..Models.Http.ClusterPrinterStatus import ClusterPrinterStatus
from ..Models.Http.PrinterSystemStatus import PrinterSystemStatus
from ..Models.Http.ClusterMaterial import ClusterMaterial


ClusterApiClientModel = TypeVar("ClusterApiClientModel", bound=BaseModel)
"""The generic type variable used to document the methods below."""


class HttpRequestMethod(StrEnum):
    GET = "GET",
    HEAD = "HEAD",
    POST = "POST",
    PUT = "PUT",
    DELETE = "DELETE",
    CONNECT = "CONNECT",
    OPTIONS = "OPTIONS",
    TRACE = "TRACE",
    PATCH = "PATCH",


class ClusterApiClient:
    """The ClusterApiClient is responsible for all network calls to local network clusters."""


    PRINTER_API_PREFIX = "/api/v1"
    CLUSTER_API_PREFIX = "/cluster-api/v1"

    AUTH_REALM = "Jedi-API"
    AUTH_QOP = "auth"
    AUTH_NONCE_LEN = 16
    AUTH_CNONCE_LEN = 8

    AUTH_MAX_TRIES = 5

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
        self._auth_id = None
        self._auth_key = None
        self._auth_tries = 0

        self._nonce_count = 1
        self._nonce = None

    def getSystem(self, on_finished: Callable) -> None:
        """Get printer system information.

        :param on_finished: The callback in case the response is successful.
        """
        url = "{}/system".format(self.PRINTER_API_PREFIX)
        reply = self._manager.get(self.createEmptyRequest(url))
        self._addCallback(reply, on_finished, PrinterSystemStatus)

    def getMaterials(self, on_finished: Callable[[List[ClusterMaterial]], Any]) -> None:
        """Get the installed materials on the printer.

        :param on_finished: The callback in case the response is successful.
        """
        url = "{}/materials".format(self.CLUSTER_API_PREFIX)
        reply = self._manager.get(self.createEmptyRequest(url))
        self._addCallback(reply, on_finished, ClusterMaterial)

    def getPrinters(self, on_finished: Callable[[List[ClusterPrinterStatus]], Any]) -> None:
        """Get the printers in the cluster.

        :param on_finished: The callback in case the response is successful.
        """
        url = "{}/printers".format(self.CLUSTER_API_PREFIX)
        reply = self._manager.get(self.createEmptyRequest(url))
        self._addCallback(reply, on_finished, ClusterPrinterStatus)

    def getPrintJobs(self, on_finished: Callable[[List[ClusterPrintJobStatus]], Any]) -> None:
        """Get the print jobs in the cluster.

        :param on_finished: The callback in case the response is successful.
        """
        url = "{}/print_jobs".format(self.CLUSTER_API_PREFIX)
        reply = self._manager.get(self.createEmptyRequest(url))
        self._addCallback(reply, on_finished, ClusterPrintJobStatus)

    def movePrintJobToTop(self, print_job_uuid: str) -> None:
        """Move a print job to the top of the queue."""

        url = "{}/print_jobs/{}/action/move".format(self.CLUSTER_API_PREFIX, print_job_uuid)
        self._manager.post(self.createEmptyRequest(url, method=HttpRequestMethod.POST), json.dumps({"to_position": 0, "list": "queued"}).encode())

    def forcePrintJob(self, print_job_uuid: str) -> None:
        """Override print job configuration and force it to be printed."""

        url = "{}/print_jobs/{}".format(self.CLUSTER_API_PREFIX, print_job_uuid)
        self._manager.put(self.createEmptyRequest(url, method=HttpRequestMethod.PUT), json.dumps({"force": True}).encode())

    def deletePrintJob(self, print_job_uuid: str) -> None:
        """Delete a print job from the queue."""

        url = "{}/print_jobs/{}".format(self.CLUSTER_API_PREFIX, print_job_uuid)
        self._manager.deleteResource(self.createEmptyRequest(url, method=HttpRequestMethod.DELETE))

    def setPrintJobState(self, print_job_uuid: str, state: str) -> None:
        """Set the state of a print job."""

        url = "{}/print_jobs/{}/action".format(self.CLUSTER_API_PREFIX, print_job_uuid)
        # We rewrite 'resume' to 'print' here because we are using the old print job action endpoints.
        action = "print" if state == "resume" else state
        self._manager.put(self.createEmptyRequest(url, method=HttpRequestMethod.PUT), json.dumps({"action": action}).encode())

    def getPrintJobPreviewImage(self, print_job_uuid: str, on_finished: Callable) -> None:
        """Get the preview image data of a print job."""

        url = "{}/print_jobs/{}/preview_image".format(self.CLUSTER_API_PREFIX, print_job_uuid)
        reply = self._manager.get(self.createEmptyRequest(url))
        self._addCallback(reply, on_finished)

    def createEmptyRequest(self, path: str, content_type: Optional[str] = "application/json", method: HttpRequestMethod = HttpRequestMethod.GET, skip_auth: bool = False) -> QNetworkRequest:
        """We override _createEmptyRequest in order to add the user credentials.

        :param path: Part added to the base-endpoint forming the total request URL (the path from the endpoint to the requested resource).
        :param content_type: The type of the body contents.
        :param method: The HTTP method to use, such as GET, POST, PUT, etc.
        :param skip_auth: Skips the authentication step if set; prevents a loop on request of authentication token.
        """
        url = QUrl("http://" + self._address + path)
        request = QNetworkRequest(url)
        if content_type:
            request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, content_type)
        if self._auth_id and self._auth_key:
            digest_str = self._makeAuthDigestHeaderPart(path, method=method)
            request.setRawHeader(b"Authorization", f"Digest {digest_str}".encode("utf-8"))
            self._nonce_count += 1
        elif not skip_auth:
            self._setupAuth()
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

    def _makeAuthDigestHeaderPart(self, url_part: str, method: HttpRequestMethod = HttpRequestMethod.GET) -> str:
        """ Make the data-part for a Digest Authentication HTTP-header.

        :param url_part: The part of the URL beyond the host name.
        :param method: The HTTP method to use, such as GET, POST, PUT, etc.
        :return: A string with the data, can be used as in `f"Digest {return_value}".encode()`.
        """

        def sha256_utf8(x: str) -> str:
            return hashlib.sha256(x.encode("utf-8")).hexdigest()

        nonce = secrets.token_hex(ClusterApiClient.AUTH_NONCE_LEN) if self._nonce is None else self._nonce
        cnonce = secrets.token_hex(ClusterApiClient.AUTH_CNONCE_LEN)
        auth_nc = f"{self._nonce_count:08x}"

        ha1 = sha256_utf8(f"{self._auth_id}:{ClusterApiClient.AUTH_REALM}:{self._auth_key}")
        ha2 = sha256_utf8(f"{method}:{url_part}")
        resp_digest = sha256_utf8(f"{ha1}:{nonce}:{auth_nc}:{cnonce}:{ClusterApiClient.AUTH_QOP}:{ha2}")
        return ", ".join([
            f'username="{self._auth_id}"',
            f'realm="{ClusterApiClient.AUTH_REALM}"',
            f'nonce="{nonce}"',
            f'uri="{url_part}"',
            f'nc={auth_nc}',
            f'cnonce="{cnonce}"',
            f'qop={ClusterApiClient.AUTH_QOP}',
            f'response="{resp_digest}"',
            f'algorithm="SHA-256"'
        ])

    def _setupAuth(self) -> None:
        """ Handles the setup process for authentication by making a temporary digest-token request to the printer API.
        """

        if self._auth_tries >= ClusterApiClient.AUTH_MAX_TRIES:
            Logger.warning("Maximum authorization temporary digest-token request tries exceeded. Is printer-firmware up to date?")
            return

        def on_finished(resp) -> None:
            self._auth_tries += 1
            try:
                auth_info = json.loads(resp.data().decode())
                self._auth_id = auth_info["id"]
                self._auth_key = auth_info["key"]
            except Exception as ex:
                Logger.warning(f"Couldn't get temporary digest token: {str(ex)}")
                return
            self._auth_tries = 0

        url = "{}/auth/request".format(self.PRINTER_API_PREFIX)
        request_body = json.dumps({
                "application": CuraApplication.getInstance().getApplicationDisplayName(),
                "user": f"user@{platform.node()}",
            }).encode("utf-8")
        reply = self._manager.post(self.createEmptyRequest(url, method=HttpRequestMethod.POST, skip_auth=True), request_body)

        self._addCallback(reply, on_finished)

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
                if reply.error() == QNetworkReply.NetworkError.AuthenticationRequiredError:
                    nonce_match = re.search(r'nonce="([^"]+)', str(reply.rawHeader(b"WWW-Authenticate")))
                    if nonce_match:
                        self._nonce = nonce_match.group(1)
                        self._nonce_count = 1
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
