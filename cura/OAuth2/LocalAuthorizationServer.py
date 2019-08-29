# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import threading
from typing import Optional, Callable, Any, TYPE_CHECKING

from UM.Logger import Logger

from cura.OAuth2.AuthorizationRequestServer import AuthorizationRequestServer
from cura.OAuth2.AuthorizationRequestHandler import AuthorizationRequestHandler

if TYPE_CHECKING:
    from cura.OAuth2.Models import AuthenticationResponse
    from cura.OAuth2.AuthorizationHelpers import AuthorizationHelpers


class LocalAuthorizationServer:
    ##  The local LocalAuthorizationServer takes care of the oauth2 callbacks.
    #   Once the flow is completed, this server should be closed down again by
    #   calling stop()
    #   \param auth_helpers An instance of the authorization helpers class.
    #   \param auth_state_changed_callback A callback function to be called when
    #   the authorization state changes.
    #   \param daemon Whether the server thread should be run in daemon mode.
    #   Note: Daemon threads are abruptly stopped at shutdown. Their resources
    #   (e.g. open files) may never be released.
    def __init__(self, auth_helpers: "AuthorizationHelpers",
                 auth_state_changed_callback: Callable[["AuthenticationResponse"], Any],
                 daemon: bool) -> None:
        self._web_server = None  # type: Optional[AuthorizationRequestServer]
        self._web_server_thread = None  # type: Optional[threading.Thread]
        self._web_server_port = auth_helpers.settings.CALLBACK_PORT
        self._auth_helpers = auth_helpers
        self._auth_state_changed_callback = auth_state_changed_callback
        self._daemon = daemon

    ##  Starts the local web server to handle the authorization callback.
    #   \param verification_code The verification code part of the OAuth2 client identification.
    def start(self, verification_code: str) -> None:
        if self._web_server:
            # If the server is already running (because of a previously aborted auth flow), we don't have to start it.
            # We still inject the new verification code though.
            self._web_server.setVerificationCode(verification_code)
            return

        if self._web_server_port is None:
            raise Exception("Unable to start server without specifying the port.")

        Logger.log("d", "Starting local web server to handle authorization callback on port %s", self._web_server_port)

        # Create the server and inject the callback and code.
        self._web_server = AuthorizationRequestServer(("0.0.0.0", self._web_server_port), AuthorizationRequestHandler)
        self._web_server.setAuthorizationHelpers(self._auth_helpers)
        self._web_server.setAuthorizationCallback(self._auth_state_changed_callback)
        self._web_server.setVerificationCode(verification_code)

        # Start the server on a new thread.
        self._web_server_thread = threading.Thread(None, self._web_server.serve_forever, daemon = self._daemon)
        self._web_server_thread.start()

    ##  Stops the web server if it was running. It also does some cleanup.
    def stop(self) -> None:
        Logger.log("d", "Stopping local oauth2 web server...")

        if self._web_server:
            try:
                self._web_server.server_close()
            except OSError:
                # OS error can happen if the socket was already closed. We really don't care about that case.
                pass
        self._web_server = None
        self._web_server_thread = None
