from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal, pyqtProperty

from UM.Logger import Logger


class ConnectionStatus(QObject):
    """Status info for some web services"""

    __instance = None  # type: Optional[ConnectionStatus]

    internetReachableChanged = pyqtSignal()

    @classmethod
    def getInstance(cls, *args, **kwargs) -> "ConnectionStatus":
        if cls.__instance is None:
            cls.__instance = cls(*args, **kwargs)
        return cls.__instance

    def __init__(self, parent: Optional["QObject"] = None) -> None:
        super().__init__(parent)

        self._is_internet_reachable = True  # type: bool

    @pyqtProperty(bool, notify = internetReachableChanged)
    def isInternetReachable(self) -> bool:
        return self._is_internet_reachable

    def setOnlineStatus(self, new_status: bool) -> None:
        old_status = self._is_internet_reachable
        self._is_internet_reachable = new_status
        if old_status != new_status:
            Logger.debug(
                "Connection status has been set to {}".format("online" if self._is_internet_reachable else "offline"))
            self.internetReachableChanged.emit()
