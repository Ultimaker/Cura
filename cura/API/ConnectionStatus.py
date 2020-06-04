from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal, QTimer, pyqtProperty
from PyQt5.QtNetwork import QNetworkReply

from UM.TaskManagement.HttpRequestManager import HttpRequestManager
from cura.UltimakerCloud import UltimakerCloudAuthentication


class ConnectionStatus(QObject):
    """Status info for some web services"""

    UPDATE_INTERVAL = 10.0  # seconds
    ULTIMAKER_CLOUD_STATUS_URL = UltimakerCloudAuthentication.CuraCloudAPIRoot + "/connect/v1/"

    __instance = None  # type: Optional[ConnectionStatus]

    internetReachableChanged = pyqtSignal()
    umCloudReachableChanged = pyqtSignal()

    @classmethod
    def getInstance(cls, *args, **kwargs) -> "ConnectionStatus":
        if cls.__instance is None:
            cls.__instance = cls(*args, **kwargs)
        return cls.__instance

    def __init__(self, parent: Optional["QObject"] = None):
        super().__init__(parent)

        self._http = HttpRequestManager.getInstance()
        self._statuses = {
            self.ULTIMAKER_CLOUD_STATUS_URL: True,
            "http://example.com": True
        }

        # Create a timer for automatic updates
        self._update_timer = QTimer()
        self._update_timer.setInterval(int(self.UPDATE_INTERVAL * 1000))
        # The timer is restarted automatically
        self._update_timer.setSingleShot(False)
        self._update_timer.timeout.connect(self._update)
        self._update_timer.start()

    @pyqtProperty(bool, notify=internetReachableChanged)
    def isInternetReachable(self) -> bool:
        # Is any of the test urls reachable?
        return any(self._statuses.values())

    def _update(self):
        for url in self._statuses.keys():
            self._http.get(
                url = url,
                callback = self._statusCallback,
                error_callback = self._statusCallback,
                timeout = 5
            )

    def _statusCallback(self, reply: QNetworkReply, error: QNetworkReply.NetworkError = None):
        url = reply.request().url().toString()
        prev_statuses = self._statuses.copy()
        self._statuses[url] = HttpRequestManager.replyIndicatesSuccess(reply, error)

        if any(self._statuses.values()) != any(prev_statuses.values()):
            self.internetReachableChanged.emit()
