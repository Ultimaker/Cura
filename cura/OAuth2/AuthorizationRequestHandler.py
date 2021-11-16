# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from http.server import BaseHTTPRequestHandler
from threading import Lock
from typing import Optional, Callable, Tuple, Dict, Any, List, TYPE_CHECKING
from urllib.parse import parse_qs, urlparse

from cura.OAuth2.Models import AuthenticationResponse, ResponseData, HTTP_STATUS
from UM.i18n import i18nCatalog

if TYPE_CHECKING:
    from cura.OAuth2.Models import ResponseStatus
    from cura.OAuth2.AuthorizationHelpers import AuthorizationHelpers

catalog = i18nCatalog("cura")

class AuthorizationRequestHandler(BaseHTTPRequestHandler):
    """This handler handles all HTTP requests on the local web server.

    It also requests the access token for the 2nd stage of the OAuth flow.
    """

    def __init__(self, request, client_address, server) -> None:
        self._do_get_lock = Lock()  # Used to make do_GET block the thread until the sub-requests are complete.

        super().__init__(request, client_address, server)

        # These values will be injected by the HTTPServer that this handler belongs to.
        self.authorization_helpers = None  # type: Optional[AuthorizationHelpers]
        self.authorization_callback = None  # type: Optional[Callable[[AuthenticationResponse], None]]
        self.verification_code = None  # type: Optional[str]

        self.state = None  # type: Optional[str]

    # CURA-6609: Some browser seems to issue a HEAD instead of GET request as the callback.
    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        self._do_get_lock.acquire()  # Only run one do_GET at a time, even if the browser makes multiple calls.
        # Extract values from the query string.
        parsed_url = urlparse(self.path)
        query = parse_qs(parsed_url.query)

        # Handle the possible requests
        # Once these are handled, the lock gets released.
        if parsed_url.path == "/callback":
            self._handleCallback(query)
        else:
            self._handleNotFound()

        self._do_get_lock.acquire(timeout = 30)  # Block for a maximum of 30 seconds before closing the connection to the browser.
        self._do_get_lock.release()

    def _handleCallback(self, query: Dict[Any, List]):
        """Handler for the callback URL redirect.

        :param query: Dict containing the HTTP query parameters.
        :return: HTTP ResponseData containing a success page to show to the user.
        """
        code = self._queryGet(query, "code")
        state = self._queryGet(query, "state")
        server_response = ResponseData(
            status = HTTP_STATUS["REDIRECT"],
            data_stream = "Redirecting...".encode("UTF-8"),
        )
        if self.authorization_helpers is not None:
            server_response.redirect_uri = self.authorization_helpers.settings.AUTH_FAILED_REDIRECT

        if state != self.state:
            token_response = AuthenticationResponse(
                success = False,
                err_message = catalog.i18nc("@message", "The provided state is not correct.")
            )
            self._responseCallback(server_response, token_response)
        elif code and self.authorization_helpers is not None and self.verification_code is not None:
            # If the code was returned we get the access token.
            server_response.redirect_uri = self.authorization_helpers.settings.AUTH_SUCCESS_REDIRECT
            self.authorization_helpers.getAccessTokenUsingAuthorizationCode(code, self.verification_code, lambda token: self._responseCallback(server_response, token))

        elif self._queryGet(query, "error_code") == "user_denied":
            # Otherwise we show an error message (probably the user clicked "Deny" in the auth dialog).
            token_response = AuthenticationResponse(
                success = False,
                err_message = catalog.i18nc("@message", "Please give the required permissions when authorizing this application.")
            )
            self._responseCallback(server_response, token_response)

        else:
            # We don't know what went wrong here, so instruct the user to check the logs.
            token_response = AuthenticationResponse(
                success = False,
                error_message = catalog.i18nc("@message", "Something unexpected happened when trying to log in, please try again.")
            )
            self._responseCallback(server_response, token_response)

    def _handleNotFound(self) -> None:
        """Handle all other non-existing server calls."""
        self._responseCallback(ResponseData(status = HTTP_STATUS["NOT_FOUND"], content_type = "text/html", data_stream = "Not found".encode("UTF-8")))
        self._do_get_lock.release()

    def _responseCallback(self, server_response: ResponseData, token_response: Optional[AuthenticationResponse] = None) -> None:
        # Send the data to the browser.
        self._sendHeaders(server_response.status, server_response.content_type, server_response.redirect_uri)

        if server_response.data_stream:
            # If there is data in the response, we send it.
            self._sendData(server_response.data_stream)

        if token_response and self.authorization_callback is not None:
            # Trigger the callback if we got a response.
            # This will cause the server to shut down, so we do it at the very end of the request handling.
            self.authorization_callback(token_response)
        self._do_get_lock.release()

    def _sendHeaders(self, status: "ResponseStatus", content_type: str, redirect_uri: str = None) -> None:
        self.send_response(status.code, status.message)
        self.send_header("Content-type", content_type)
        if redirect_uri:
            self.send_header("Location", redirect_uri)
        self.end_headers()

    def _sendData(self, data: bytes) -> None:
        self.wfile.write(data)

    @staticmethod
    def _queryGet(query_data: Dict[Any, List], key: str, default: Optional[str] = None) -> Optional[str]:
        """Convenience helper for getting values from a pre-parsed query string"""

        return query_data.get(key, [default])[0]
