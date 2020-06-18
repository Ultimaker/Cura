from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal, pyqtProperty

from UM.TaskManagement.HttpRequestManager import HttpRequestManager


class ConnectionStatus(QObject):
    """Provides an estimation of whether internet is reachable

    Estimation is updated with every request through HttpRequestManager.
    Acts as a proxy to HttpRequestManager.internetReachableChanged without
    exposing the HttpRequestManager in its entirety.
    """

    __instance = None  # type: Optional[ConnectionStatus]

    internetReachableChanged = pyqtSignal()

    @classmethod
    def getInstance(cls, *args, **kwargs) -> "ConnectionStatus":
        if cls.__instance is None:
            cls.__instance = cls(*args, **kwargs)
        return cls.__instance

    def __init__(self, parent: Optional["QObject"] = None) -> None:
        super().__init__(parent)

        manager = HttpRequestManager.getInstance()
        self._is_internet_reachable = manager.isInternetReachable  # type: bool
        manager.internetReachableChanged.connect(self._onInternetReachableChanged)

    @pyqtProperty(bool, notify = internetReachableChanged)
    def isInternetReachable(self) -> bool:
        return self._is_internet_reachable

    def _onInternetReachableChanged(self, reachable: bool):
        if reachable != self._is_internet_reachable:
            self._is_internet_reachable = reachable
            self.internetReachableChanged.emit()

