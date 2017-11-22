from UM.Application import Application
from UM.Logger import Logger

from cura.PrinterOutputDevice import PrinterOutputDevice, ConnectionState

from PyQt5.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkRequest, QNetworkAccessManager, QNetworkReply
from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject, QTimer, pyqtSignal, QUrl

from time import time
from typing import Callable, Any
from enum import IntEnum


class AuthState(IntEnum):
    NotAuthenticated = 1
    AuthenticationRequested = 2
    Authenticated = 3
    AuthenticationDenied = 4
    AuthenticationReceived = 5


class NetworkedPrinterOutputDevice(PrinterOutputDevice):
    authenticationStateChanged = pyqtSignal()
    def __init__(self, device_id, address: str, properties, parent = None):
        super().__init__(device_id = device_id, parent = parent)
        self._manager = None
        self._last_manager_create_time = None
        self._recreate_network_manager_time = 30
        self._timeout_time = 10  # After how many seconds of no response should a timeout occur?

        self._last_response_time = None
        self._last_request_time = None

        self._api_prefix = ""
        self._address = address
        self._properties = properties
        self._user_agent = "%s/%s " % (Application.getInstance().getApplicationName(), Application.getInstance().getVersion())

        self._onFinishedCallbacks = {}
        self._authentication_state = AuthState.NotAuthenticated

    def setAuthenticationState(self, authentication_state):
        if self._authentication_state != authentication_state:
            self._authentication_state = authentication_state
            self.authenticationStateChanged.emit()

    @pyqtProperty(int, notify=authenticationStateChanged)
    def authenticationState(self):
        return self._authentication_state

    def _update(self):
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
            self.setConnectionState(ConnectionState.closed)
            # We need to check if the manager needs to be re-created. If we don't, we get some issues when OSX goes to
            # sleep.
            if time_since_last_response > self._recreate_network_manager_time:
                if self._last_manager_create_time is None:
                    self._createNetworkManager()
                if time() - self._last_manager_create_time > self._recreate_network_manager_time:
                    self._createNetworkManager()

        return True

    def _createEmptyRequest(self, target):
        url = QUrl("http://" + self._address + self._api_prefix + target)
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        request.setHeader(QNetworkRequest.UserAgentHeader, self._user_agent)
        return request

    def _put(self, target: str, data: str, onFinished: Callable[[Any, QNetworkReply], None]):
        if self._manager is None:
            self._createNetworkManager()
        request = self._createEmptyRequest(target)
        self._last_request_time = time()
        reply = self._manager.put(request, data.encode())
        self._onFinishedCallbacks[reply.url().toString() + str(reply.operation())] = onFinished

    def _get(self, target: str, onFinished: Callable[[Any, QNetworkReply], None]):
        if self._manager is None:
            self._createNetworkManager()
        request = self._createEmptyRequest(target)
        self._last_request_time = time()
        reply = self._manager.get(request)
        self._onFinishedCallbacks[reply.url().toString() + str(reply.operation())] = onFinished

    def _delete(self, target: str, onFinished: Callable[[Any, QNetworkReply], None]):
        if self._manager is None:
            self._createNetworkManager()
        self._last_request_time = time()
        pass

    def _post(self, target: str, data: str, onFinished: Callable[[Any, QNetworkReply], None], onProgress: Callable = None):
        if self._manager is None:
            self._createNetworkManager()
        request = self._createEmptyRequest(target)
        self._last_request_time = time()
        reply = self._manager.post(request, data)
        if onProgress is not None:
            reply.uploadProgress.connect(onProgress)
        self._onFinishedCallbacks[reply.url().toString() + str(reply.operation())] = onFinished

    def _onAuthenticationRequired(self, reply, authenticator):
        Logger.log("w", "Request to {url} required authentication, which was not implemented".format(url = reply.url().toString()))

    def _createNetworkManager(self):
        Logger.log("d", "Creating network manager")
        if self._manager:
            self._manager.finished.disconnect(self.__handleOnFinished)
            #self._manager.networkAccessibleChanged.disconnect(self._onNetworkAccesibleChanged)
            self._manager.authenticationRequired.disconnect(self._onAuthenticationRequired)

        self._manager = QNetworkAccessManager()
        self._manager.finished.connect(self.__handleOnFinished)
        self._last_manager_create_time = time()
        self._manager.authenticationRequired.connect(self._onAuthenticationRequired)
        #self._manager.networkAccessibleChanged.connect(self._onNetworkAccesibleChanged)  # for debug purposes

    def __handleOnFinished(self, reply: QNetworkReply):
        if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) is None:
            # No status code means it never even reached remote.
            return

        self._last_response_time = time()

        if self._connection_state == ConnectionState.connecting:
            self.setConnectionState(ConnectionState.connected)

        try:
            self._onFinishedCallbacks[reply.url().toString() + str(reply.operation())](reply)
        except Exception:
            Logger.logException("w", "something went wrong with callback")

    @pyqtSlot(str, result=str)
    def getProperty(self, key):
        key = key.encode("utf-8")
        if key in self._properties:
            return self._properties.get(key, b"").decode("utf-8")
        else:
            return ""

    ##  Get the unique key of this machine
    #   \return key String containing the key of the machine.
    @pyqtProperty(str, constant=True)
    def key(self):
        return self._id

    ##  The IP address of the printer.
    @pyqtProperty(str, constant=True)
    def address(self):
        return self._properties.get(b"address", b"").decode("utf-8")

    ##  Name of the printer (as returned from the ZeroConf properties)
    @pyqtProperty(str, constant=True)
    def name(self):
        return self._properties.get(b"name", b"").decode("utf-8")

    ##  Firmware version (as returned from the ZeroConf properties)
    @pyqtProperty(str, constant=True)
    def firmwareVersion(self):
        return self._properties.get(b"firmware_version", b"").decode("utf-8")

    ## IPadress of this printer
    @pyqtProperty(str, constant=True)
    def ipAddress(self):
        return self._address