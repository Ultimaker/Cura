# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from http.server import HTTPServer
from typing import Callable, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from cura.OAuth2.Models import AuthenticationResponse
    from cura.OAuth2.AuthorizationHelpers import AuthorizationHelpers


class AuthorizationRequestServer(HTTPServer):
    """The authorization request callback handler server.

    This subclass is needed to be able to pass some data to the request handler. This cannot be done on the request
    handler directly as the HTTPServer creates an instance of the handler after init.
    """

    def setAuthorizationHelpers(self, authorization_helpers: "AuthorizationHelpers") -> None:
        """Set the authorization helpers instance on the request handler."""

        self.RequestHandlerClass.authorization_helpers = authorization_helpers  # type: ignore

    def setAuthorizationCallback(self, authorization_callback: Callable[["AuthenticationResponse"], Any]) -> None:
        """Set the authorization callback on the request handler."""

        self.RequestHandlerClass.authorization_callback = authorization_callback  # type: ignore

    def setVerificationCode(self, verification_code: str) -> None:
        """Set the verification code on the request handler."""

        self.RequestHandlerClass.verification_code = verification_code  # type: ignore

    def setState(self, state: str) -> None:
        self.RequestHandlerClass.state = state  # type: ignore
