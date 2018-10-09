# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.FileHandler.FileHandler import FileHandler #For typing.
from UM.Logger import Logger
from UM.Scene.SceneNode import SceneNode #For typing.
from cura.CuraApplication import CuraApplication

from cura.PrinterOutputDevice import PrinterOutputDevice, ConnectionState

from PyQt5.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkRequest, QNetworkAccessManager, QNetworkReply, QAuthenticator
from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject, QUrl, QCoreApplication
from time import time
from typing import Any, Callable, Dict, List, Optional
from enum import IntEnum

import os  # To get the username
import gzip

class AuthState(IntEnum):
    NotAuthenticated = 1
    AuthenticationRequested = 2
    Authenticated = 3
    AuthenticationDenied = 4
    AuthenticationReceived = 5


class NetworkedPrinterOutputDevice(PrinterOutputDevice):
    authenticationStateChanged = pyqtSignal()

    def __init__(self, device_id, address: str, properties: Dict[bytes, bytes], parent: QObject = None) -> None:
        super().__init__(device_id = device_id, parent = parent)
        self._manager = None    # type: Optional[QNetworkAccessManager]
        self._last_manager_create_time = None       # type: Optional[float]
        self._recreate_network_manager_time = 30
        self._timeout_time = 10  # After how many seconds of no response should a timeout occur?

        self._last_response_time = None     # type: Optional[float]
        self._last_request_time = None      # type: Optional[float]

        self._api_prefix = ""
        self._address = address
        self._properties = properties
        self._user_agent = "%s/%s " % (CuraApplication.getInstance().getApplicationName(), CuraApplication.getInstance().getVersion())

        self._onFinishedCallbacks = {}      # type: Dict[str, Callable[[QNetworkReply], None]]
        self._authentication_state = AuthState.NotAuthenticated

        # QHttpMultiPart objects need to be kept alive and not garbage collected during the
        # HTTP which uses them. We hold references to these QHttpMultiPart objects here.
        self._kept_alive_multiparts = {}        # type: Dict[QNetworkReply, QHttpMultiPart]

        self._sending_gcode = False
        self._compressing_gcode = False
        self._gcode = []                    # type: List[str]
        self._connection_state_before_timeout = None    # type: Optional[ConnectionState]

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
                if self._last_manager_create_time is None:
                    self._createNetworkManager()
                elif time() - self._last_manager_create_time > self._recreate_network_manager_time:
                    self._createNetworkManager()
                assert(self._manager is not None)
        elif self._connection_state == ConnectionState.closed:
            # Go out of timeout.
            if self._connection_state_before_timeout is not None:   # sanity check, but it should never be None here
                self.setConnectionState(self._connection_state_before_timeout)
                self._connection_state_before_timeout = None

    def _createEmptyRequest(self, target: str, content_type: Optional[str] = "application/json") -> QNetworkRequest:
        url = QUrl("http://" + self._address + self._api_prefix + target)
        request = QNetworkRequest(url)
        if content_type is not None:
            request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        request.setHeader(QNetworkRequest.UserAgentHeader, self._user_agent)
        return request

    def _createFormPart(self, content_header: str, data: bytes, content_type: Optional[str] = None) -> QHttpPart:
        part = QHttpPart()

        if not content_header.startswith("form-data;"):
            content_header = "form_data; " + content_header
        part.setHeader(QNetworkRequest.ContentDispositionHeader, content_header)

        if content_type is not None:
            part.setHeader(QNetworkRequest.ContentTypeHeader, content_type)

        part.setBody(data)
        return part

    ##  Convenience function to get the username from the OS.
    #   The code was copied from the getpass module, as we try to use as little dependencies as possible.
    def _getUserName(self) -> str:
        for name in ("LOGNAME", "USER", "LNAME", "USERNAME"):
            user = os.environ.get(name)
            if user:
                return user
        return "Unknown User"  # Couldn't find out username.

    def _clearCachedMultiPart(self, reply: QNetworkReply) -> None:
        if reply in self._kept_alive_multiparts:
            del self._kept_alive_multiparts[reply]

    def _validateManager(self) -> None:
        if self._manager is None:
            self._createNetworkManager()
        assert (self._manager is not None)

    def put(self, target: str, data: str, on_finished: Optional[Callable[[QNetworkReply], None]]) -> None:
        self._validateManager()
        request = self._createEmptyRequest(target)
        self._last_request_time = time()
        if self._manager is not None:
            reply = self._manager.put(request, data.encode())
            self._registerOnFinishedCallback(reply, on_finished)
        else:
            Logger.log("e", "Could not find manager.")

    def delete(self, target: str, on_finished: Optional[Callable[[QNetworkReply], None]]) -> None:
        self._validateManager()
        request = self._createEmptyRequest(target)
        self._last_request_time = time()
        if self._manager is not None:
            reply = self._manager.deleteResource(request)
            self._registerOnFinishedCallback(reply, on_finished)
        else:
            Logger.log("e", "Could not find manager.")

    def get(self, target: str, on_finished: Optional[Callable[[QNetworkReply], None]]) -> None:
        self._validateManager()
        request = self._createEmptyRequest(target)
        self._last_request_time = time()
        if self._manager is not None:
            reply = self._manager.get(request)
            self._registerOnFinishedCallback(reply, on_finished)
        else:
            Logger.log("e", "Could not find manager.")

    def post(self, target: str, data: str, on_finished: Optional[Callable[[QNetworkReply], None]], on_progress: Callable = None) -> None:
        self._validateManager()
        request = self._createEmptyRequest(target)
        self._last_request_time = time()
        if self._manager is not None:
            reply = self._manager.post(request, data)
            if on_progress is not None:
                reply.uploadProgress.connect(on_progress)
            self._registerOnFinishedCallback(reply, on_finished)
        else:
            Logger.log("e", "Could not find manager.")

    def postFormWithParts(self, target: str, parts: List[QHttpPart], on_finished: Optional[Callable[[QNetworkReply], None]], on_progress: Callable = None) -> QNetworkReply:
        self._validateManager()
        request = self._createEmptyRequest(target, content_type=None)
        multi_post_part = QHttpMultiPart(QHttpMultiPart.FormDataType)
        for part in parts:
            multi_post_part.append(part)

        self._last_request_time = time()

        if self._manager is not None:
            reply = self._manager.post(request, multi_post_part)

            self._kept_alive_multiparts[reply] = multi_post_part

            if on_progress is not None:
                reply.uploadProgress.connect(on_progress)
            self._registerOnFinishedCallback(reply, on_finished)

            return reply
        else:
            Logger.log("e", "Could not find manager.")

    def postForm(self, target: str, header_data: str, body_data: bytes, on_finished: Optional[Callable[[QNetworkReply], None]], on_progress: Callable = None) -> None:
        post_part = QHttpPart()
        post_part.setHeader(QNetworkRequest.ContentDispositionHeader, header_data)
        post_part.setBody(body_data)

        self.postFormWithParts(target, [post_part], on_finished, on_progress)

    def _onAuthenticationRequired(self, reply: QNetworkReply, authenticator: QAuthenticator) -> None:
        Logger.log("w", "Request to {url} required authentication, which was not implemented".format(url = reply.url().toString()))

    def _createNetworkManager(self) -> None:
        Logger.log("d", "Creating network manager")
        if self._manager:
            self._manager.finished.disconnect(self.__handleOnFinished)
            self._manager.authenticationRequired.disconnect(self._onAuthenticationRequired)

        self._manager = QNetworkAccessManager()
        self._manager.finished.connect(self.__handleOnFinished)
        self._last_manager_create_time = time()
        self._manager.authenticationRequired.connect(self._onAuthenticationRequired)

        if self._properties.get(b"temporary", b"false") != b"true":
            CuraApplication.getInstance().getMachineManager().checkCorrectGroupName(self.getId(), self.name)

    def _registerOnFinishedCallback(self, reply: QNetworkReply, on_finished: Optional[Callable[[QNetworkReply], None]]) -> None:
        if on_finished is not None:
            self._onFinishedCallbacks[reply.url().toString() + str(reply.operation())] = on_finished

    def __handleOnFinished(self, reply: QNetworkReply) -> None:
        # Due to garbage collection, we need to cache certain bits of post operations.
        # As we don't want to keep them around forever, delete them if we get a reply.
        if reply.operation() == QNetworkAccessManager.PostOperation:
            self._clearCachedMultiPart(reply)

        if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) is None:
            # No status code means it never even reached remote.
            return

        self._last_response_time = time()

        if self._connection_state == ConnectionState.connecting:
            self.setConnectionState(ConnectionState.connected)

        callback_key = reply.url().toString() + str(reply.operation())
        try:
            if callback_key in self._onFinishedCallbacks:
                self._onFinishedCallbacks[callback_key](reply)
        except Exception:
            Logger.logException("w", "something went wrong with callback")

    @pyqtSlot(str, result=str)
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

    ## IP adress of this printer
    @pyqtProperty(str, constant = True)
    def ipAddress(self) -> str:
        return self._address
