# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import sys
import threading
from typing import Any, Callable, Optional, TYPE_CHECKING

from UM.Logger import Logger

got_server_type = False
try:
    from cura.OAuth2.AuthorizationRequestServer import AuthorizationRequestServer
    from cura.OAuth2.AuthorizationRequestHandler import AuthorizationRequestHandler
    got_server_type = True
except PermissionError:  # Bug in http.server: Can't access MIME types. This will prevent the user from logging in. See Sentry bug Cura-3Q.
    Logger.error("Can't start a server due to a PermissionError when starting the http.server.")

if TYPE_CHECKING:
    from cura.OAuth2.Models import AuthenticationResponse
    from cura.OAuth2.AuthorizationHelpers import AuthorizationHelpers


class LocalAuthorizationServer:
    def __init__(self, auth_helpers: "AuthorizationHelpers",
                 auth_state_changed_callback: Callable[["AuthenticationResponse"], Any],
                 daemon: bool) -> None:
        """The local LocalAuthorizationServer takes care of the oauth2 callbacks.

        Once the flow is completed, this server should be closed down again by calling
        :py:meth:`cura.OAuth2.LocalAuthorizationServer.LocalAuthorizationServer.stop()`

        :param auth_helpers: An instance of the authorization helpers class.
        :param auth_state_changed_callback: A callback function to be called when the authorization state changes.
        :param daemon: Whether the server thread should be run in daemon mode.

        .. note::

            Daemon threads are abruptly stopped at shutdown. Their resources (e.g. open files) may never be released.
        """

        self._web_server = None  # type: Optional[AuthorizationRequestServer]
        self._web_server_thread = None  # type: Optional[threading.Thread]
        self._web_server_port = auth_helpers.settings.CALLBACK_PORT
        self._auth_helpers = auth_helpers
        self._auth_state_changed_callback = auth_state_changed_callback
        self._daemon = daemon

    def start(self, verification_code: str, state: str) -> None:
        """Starts the local web server to handle the authorization callback.

        :param verification_code: The verification code part of the OAuth2 client identification.
        :param state: The unique state code (to ensure that the request we get back is really from the server.
        """

        if self._web_server:
            # If the server is already running (because of a previously aborted auth flow), we don't have to start it.
            # We still inject the new verification code though.
            self._web_server.setVerificationCode(verification_code)
            return

        if self._web_server_port is None:
            raise Exception("Unable to start server without specifying the port.")

        Logger.log("d", "Starting local web server to handle authorization callback on port %s", self._web_server_port)

        # Create the server and inject the callback and code.
        if got_server_type:
            self._web_server = AuthorizationRequestServer(("0.0.0.0", self._web_server_port), AuthorizationRequestHandler)
            self._web_server.setAuthorizationHelpers(self._auth_helpers)
            self._web_server.setAuthorizationCallback(self._auth_state_changed_callback)
            self._web_server.setVerificationCode(verification_code)
            self._web_server.setState(state)

            # Start the server on a new thread.
            self._web_server_thread = threading.Thread(None, self._serve_forever, daemon = self._daemon)
            self._web_server_thread.start()

    def stop(self) -> None:
        """Stops the web server if it was running. It also does some cleanup."""

        Logger.log("d", "Stopping local oauth2 web server...")

        if self._web_server:
            try:
                self._web_server.shutdown()
                self._web_server.server_close()
            except OSError:
                # OS error can happen if the socket was already closed. We really don't care about that case.
                pass
        self._web_server = None
        self._web_server_thread = None

    def _serve_forever(self) -> None:
        """
        If the platform is windows, this function calls the serve_forever function of the _web_server, catching any
        OSErrors that may occur in the thread, thus making the reported message more log-friendly.
        If it is any other platform, it just calls the serve_forever function immediately.

        :return: None
        """
        if self._web_server:
            if sys.platform == "win32":
                try:
                    self._web_server.serve_forever()
                except OSError as e:
                    Logger.warning(str(e))
            else:
                # Leave the default behavior in non-windows platforms
                self._web_server.serve_forever()
