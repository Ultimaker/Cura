# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import os
import gzip
from time import time
from typing import Dict, List, Optional
from enum import IntEnum

from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject, QCoreApplication

from UM.FileHandler.FileHandler import FileHandler
from UM.Scene.SceneNode import SceneNode
from cura.NetworkClient import NetworkClient
from cura.PrinterOutputDevice import PrinterOutputDevice, ConnectionState


class AuthState(IntEnum):
    NotAuthenticated = 1
    AuthenticationRequested = 2
    Authenticated = 3
    AuthenticationDenied = 4
    AuthenticationReceived = 5


class NetworkedPrinterOutputDevice(PrinterOutputDevice, NetworkClient):
    authenticationStateChanged = pyqtSignal()

    def __init__(self, device_id, address: str, properties: Dict[bytes, bytes], parent: QObject = None) -> None:
        PrinterOutputDevice.__init__(self, device_id = device_id, parent = parent)
        NetworkClient.__init__(self)
        
        self._api_prefix = ""
        self._address = address
        self._properties = properties
        self._authentication_state = AuthState.NotAuthenticated
        self._sending_gcode = False
        self._compressing_gcode = False
        self._gcode = []                    # type: List[str]
        
        self._connection_state_before_timeout = None    # type: Optional[ConnectionState]
        self._timeout_time = 10  # After how many seconds of no response should a timeout occur?
        self._recreate_network_manager_time = 30
        
    ##  Override creating empty request to compile the full URL.
    #   Needed to keep NetworkedPrinterOutputDevice backwards compatible after refactoring NetworkClient out of it.
    def _createEmptyRequest(self, target: str, content_type: Optional[str] = "application/json") -> QNetworkRequest:
        return super()._createEmptyRequest("http://" + self._address + self._api_prefix + target, content_type)

    def requestWrite(self, nodes: List[SceneNode], file_name: Optional[str] = None, limit_mimetypes: bool = False, file_handler: Optional[FileHandler] = None, **kwargs: str) -> None:
        raise NotImplementedError("requestWrite needs to be implemented")

    def setAuthenticationState(self, authentication_state: AuthState) -> None:
        if self._authentication_state != authentication_state:
            self._authentication_state = authentication_state
            self.authenticationStateChanged.emit()

    @pyqtProperty(int, notify = authenticationStateChanged)
    def authenticationState(self) -> AuthState:
        return self._authentication_state

    def _compressDataAndNotifyQt(self, data_to_append: str) -> bytes:
        compressed_data = gzip.compress(data_to_append.encode("utf-8"))
        self._progress_message.setProgress(-1)  # Tickle the message so that it's clear that it's still being used.
        QCoreApplication.processEvents()  # Ensure that the GUI does not freeze.

        # Pretend that this is a response, as zipping might take a bit of time.
        # If we don't do this, the device might trigger a timeout.
        self._last_response_time = time()
        return compressed_data

    def _compressGCode(self) -> Optional[bytes]:
        self._compressing_gcode = True

        ## Mash the data into single string
        max_chars_per_line = int(1024 * 1024 / 4)  # 1/4 MB per line.
        file_data_bytes_list = []
        batched_lines = []
        batched_lines_count = 0

        for line in self._gcode:
            if not self._compressing_gcode:
                self._progress_message.hide()
                # Stop trying to zip / send as abort was called.
                return None

            # if the gcode was read from a gcode file, self._gcode will be a list of all lines in that file.
            # Compressing line by line in this case is extremely slow, so we need to batch them.
            batched_lines.append(line)
            batched_lines_count += len(line)

            if batched_lines_count >= max_chars_per_line:
                file_data_bytes_list.append(self._compressDataAndNotifyQt("".join(batched_lines)))
                batched_lines = []
                batched_lines_count = 0

        # Don't miss the last batch (If any)
        if len(batched_lines) != 0:
            file_data_bytes_list.append(self._compressDataAndNotifyQt("".join(batched_lines)))

        self._compressing_gcode = False
        return b"".join(file_data_bytes_list)

    def _update(self) -> None:
        if self._last_response_time:
            time_since_last_response = time() - self._last_response_time
        else:
            time_since_last_response = 0

        if self._last_request_time:
            time_since_last_request = time() - self._last_request_time
        else:
            time_since_last_request = float("inf")  # An irrelevantly large number of seconds

        if time_since_last_response > self._timeout_time >= time_since_last_request:
            # Go (or stay) into timeout.
            if self._connection_state_before_timeout is None:
                self._connection_state_before_timeout = self._connection_state

            self.setConnectionState(ConnectionState.closed)

            # We need to check if the manager needs to be re-created. If we don't, we get some issues when OSX goes to
            # sleep.
            if time_since_last_response > self._recreate_network_manager_time:
                if self._last_manager_create_time is None or time() - self._last_manager_create_time > self._recreate_network_manager_time:
                    self._createNetworkManager()
                assert(self._manager is not None)
        elif self._connection_state == ConnectionState.closed:
            # Go out of timeout.
            if self._connection_state_before_timeout is not None:   # sanity check, but it should never be None here
                self.setConnectionState(self._connection_state_before_timeout)
                self._connection_state_before_timeout = None

    ##  Convenience function to get the username from the OS.
    #   The code was copied from the getpass module, as we try to use as little dependencies as possible.
    def _getUserName(self) -> str:
        for name in ("LOGNAME", "USER", "LNAME", "USERNAME"):
            user = os.environ.get(name)
            if user:
                return user
        return "Unknown User"  # Couldn't find out username.

    @pyqtSlot(str, result = str)
    def getProperty(self, key: str) -> str:
        bytes_key = key.encode("utf-8")
        if bytes_key in self._properties:
            return self._properties.get(bytes_key, b"").decode("utf-8")
        else:
            return ""

    def getProperties(self):
        return self._properties

    ##  Get the unique key of this machine
    #   \return key String containing the key of the machine.
    @pyqtProperty(str, constant = True)
    def key(self) -> str:
        return self._id

    ##  The IP address of the printer.
    @pyqtProperty(str, constant = True)
    def address(self) -> str:
        return self._properties.get(b"address", b"").decode("utf-8")

    ##  Name of the printer (as returned from the ZeroConf properties)
    @pyqtProperty(str, constant = True)
    def name(self) -> str:
        return self._properties.get(b"name", b"").decode("utf-8")

    ##  Firmware version (as returned from the ZeroConf properties)
    @pyqtProperty(str, constant = True)
    def firmwareVersion(self) -> str:
        return self._properties.get(b"firmware_version", b"").decode("utf-8")

    @pyqtProperty(str, constant = True)
    def printerType(self) -> str:
        return self._properties.get(b"printer_type", b"Unknown").decode("utf-8")

    ## IP address of this printer
    @pyqtProperty(str, constant = True)
    def ipAddress(self) -> str:
        return self._address

    def __handleOnFinished(self, reply: QNetworkReply) -> None:
        super().__handleOnFinished(reply)
        
        # Since we got a reply from the network manager we can now be sure we are actually connected.
        if self._connection_state == ConnectionState.connecting:
            self.setConnectionState(ConnectionState.connected)
