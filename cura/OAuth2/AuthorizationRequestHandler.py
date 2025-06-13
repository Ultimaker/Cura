# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from http.server import BaseHTTPRequestHandler
from threading import Lock  # To turn an asynchronous call synchronous.
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
        super().__init__(request, client_address, server)

        # These values will be injected by the HTTPServer that this handler belongs to.
        self.authorization_helpers: Optional[AuthorizationHelpers] = None
        self.authorization_callback: Optional[Callable[[AuthenticationResponse], None]] = None
        self.verification_code: Optional[str] = None

        self.state: Optional[str] = None

    # CURA-6609: Some browser seems to issue a HEAD instead of GET request as the callback.
    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        # Extract values from the query string.
        parsed_url = urlparse(self.path)
        query = parse_qs(parsed_url.query)

        # Handle the possible requests
        if parsed_url.path == "/callback":
            server_response, token_response = self._handleCallback(query)
        else:
            server_response = self._handleNotFound()
            token_response = None

        # Send the data to the browser.
        self._sendHeaders(server_response.status, server_response.content_type, server_response.redirect_uri)

        if server_response.data_stream:
            # If there is data in the response, we send it.
            self._sendData(server_response.data_stream)

        if token_response and self.authorization_callback is not None:
            # Trigger the callback if we got a response.
            # This will cause the server to shut down, so we do it at the very end of the request handling.
            self.authorization_callback(token_response)

    def _handleCallback(self, query: Dict[Any, List]) -> Tuple[ResponseData, Optional[AuthenticationResponse]]:
        """Handler for the callback URL redirect.

        :param query: Dict containing the HTTP query parameters.
        :return: HTTP ResponseData containing a success page to show to the user.
        """

        code = self._queryGet(query, "code")
        state = self._queryGet(query, "state")
        if state != self.state:
            token_response = AuthenticationResponse(
                success = False,
                err_message = catalog.i18nc("@message", "The provided state is not correct.")
            )
        elif code and self.authorization_helpers is not None and self.verification_code is not None:
            token_response = AuthenticationResponse(
                success = False,
                err_message = catalog.i18nc("@message", "Timeout when authenticating with the account server.")
            )
            # If the code was returned we get the access token.
            lock = Lock()
            lock.acquire()

            def callback(response: AuthenticationResponse) -> None:
                nonlocal token_response
                token_response = response
                lock.release()
            self.authorization_helpers.getAccessTokenUsingAuthorizationCode(code, self.verification_code, callback)
            lock.acquire(timeout = 60)  # Block thread until request is completed (which releases the lock). If not acquired, the timeout message stays.

        elif self._queryGet(query, "error_code") == "user_denied":
            # Otherwise we show an error message (probably the user clicked "Deny" in the auth dialog).
            token_response = AuthenticationResponse(
                success = False,
                err_message = catalog.i18nc("@message", "Please give the required permissions when authorizing this application.")
            )

        else:
            # We don't know what went wrong here, so instruct the user to check the logs.
            token_response = AuthenticationResponse(
                success = False,
                error_message = catalog.i18nc("@message", "Something unexpected happened when trying to log in, please try again.")
            )
        if self.authorization_helpers is None:
            return ResponseData(), token_response

        return ResponseData(
            status = HTTP_STATUS["REDIRECT"],
            data_stream = b"Redirecting...",
            redirect_uri = self.authorization_helpers.settings.AUTH_SUCCESS_REDIRECT if token_response.success else
            self.authorization_helpers.settings.AUTH_FAILED_REDIRECT
        ), token_response

    @staticmethod
    def _handleNotFound() -> ResponseData:
        """Handle all other non-existing server calls."""

        return ResponseData(status = HTTP_STATUS["NOT_FOUND"], content_type = "text/html", data_stream = b"Not found.")

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
