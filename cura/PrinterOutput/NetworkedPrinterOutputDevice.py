from UM.Application import Application
from cura.PrinterOutputDevice import PrinterOutputDevice

from PyQt5.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkRequest, QNetworkAccessManager, QNetworkReply
from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject, QTimer, pyqtSignal, QUrl

from time import time
from typing import Callable


class NetworkedPrinterOutputDevice(PrinterOutputDevice):
    def __init__(self, device_id, address: str, properties, parent = None):
        super().__init__(device_id = device_id, parent = parent)
        self._manager = None
        self._createNetworkManager()
        self._last_response_time = time()
        self._last_request_time = None
        self._api_prefix = ""
        self._address = address
        self._properties = properties
        self._user_agent = "%s/%s " % (Application.getInstance().getApplicationName(), Application.getInstance().getVersion())

        self._onFinishedCallbacks = {}

    def _update(self):
        if not self._manager.networkAccessible():
            pass  # TODO: no internet connection.

        pass

    def _createEmptyRequest(self, target):
        url = QUrl("http://" + self._address + self._api_prefix + target)
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        request.setHeader(QNetworkRequest.UserAgentHeader, self._user_agent)
        return request

    def _put(self, target: str, data: str, onFinished: Callable):
        request = self._createEmptyRequest(target)
        self._onFinishedCallbacks[request] = onFinished
        self._manager.put(request, data.encode())

    def _get(self, target: str, onFinished: Callable):
        request = self._createEmptyRequest(target)
        self._onFinishedCallbacks[request] = onFinished
        self._manager.get(request)

    def _delete(self, target: str, onFinished: Callable):
        pass

    def _post(self, target: str, data: str, onFinished: Callable, onProgress: Callable):
        pass

    def _createNetworkManager(self):
        if self._manager:
            self._manager.finished.disconnect(self.__handleOnFinished)
            #self._manager.networkAccessibleChanged.disconnect(self._onNetworkAccesibleChanged)
            #self._manager.authenticationRequired.disconnect(self._onAuthenticationRequired)

        self._manager = QNetworkAccessManager()
        self._manager.finished.connect(self.__handleOnFinished)
        #self._manager.authenticationRequired.connect(self._onAuthenticationRequired)
        #self._manager.networkAccessibleChanged.connect(self._onNetworkAccesibleChanged)  # for debug purposes

    def __handleOnFinished(self, reply: QNetworkReply):
        self._last_response_time = time()
        try:
            self._onFinishedCallbacks[reply.request()](reply)
            del self._onFinishedCallbacks[reply.request]  # Remove the callback.
        except Exception as e:
            print("Something went wrong with callback", e)
        pass

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