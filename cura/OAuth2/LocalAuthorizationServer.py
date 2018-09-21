# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import threading
from http.server import HTTPServer
from typing import Optional, Callable

# As this module is specific for Cura plugins, we can rely on these imports.
from UM.Logger import Logger

# Plugin imports need to be relative to work in final builds.
from cura.OAuth2.AuthorizationHelpers import AuthorizationHelpers
from cura.OAuth2.AuthorizationRequestServer import AuthorizationRequestServer
from cura.OAuth2.AuthorizationRequestHandler import AuthorizationRequestHandler
from cura.OAuth2.Models import AuthenticationResponse


class LocalAuthorizationServer:
    def __init__(self, auth_helpers: "AuthorizationHelpers",
                 auth_state_changed_callback: "Callable[[AuthenticationResponse], any]",
                 daemon: bool):
        """
        :param auth_helpers: An instance of the authorization helpers class.
        :param auth_state_changed_callback: A callback function to be called when the authorization state changes.
        :param daemon: Whether the server thread should be run in daemon mode. Note: Daemon threads are abruptly stopped
            at shutdown. Their resources (e.g. open files) may never be released.
        """
        self._web_server = None  # type: Optional[HTTPServer]
        self._web_server_thread = None  # type: Optional[threading.Thread]
        self._web_server_port = auth_helpers.settings.CALLBACK_PORT
        self._auth_helpers = auth_helpers
        self._auth_state_changed_callback = auth_state_changed_callback
        self._daemon = daemon

    def start(self, verification_code: "str") -> None:
        """
        Starts the local web server to handle the authorization callback.
        :param verification_code: The verification code part of the OAuth2 client identification.
        """
        if self._web_server:
            # If the server is already running (because of a previously aborted auth flow), we don't have to start it.
            # We still inject the new verification code though.
            self._web_server.setVerificationCode(verification_code)
            return

        Logger.log("d", "Starting local web server to handle authorization callback on port %s",
                   self._web_server_port)

        # Create the server and inject the callback and code.
        self._web_server = AuthorizationRequestServer(("0.0.0.0", self._web_server_port),
                                                      AuthorizationRequestHandler)
        self._web_server.setAuthorizationHelpers(self._auth_helpers)
        self._web_server.setAuthorizationCallback(self._auth_state_changed_callback)
        self._web_server.setVerificationCode(verification_code)

        # Start the server on a new thread.
        self._web_server_thread = threading.Thread(None, self._web_server.serve_forever, daemon = self._daemon)
        self._web_server_thread.start()

    def stop(self) -> None:
        """ Stops the web server if it was running. Also deletes the objects. """

        Logger.log("d", "Stopping local web server...")

        if self._web_server:
            self._web_server.server_close()
        self._web_server = None
        self._web_server_thread = None
