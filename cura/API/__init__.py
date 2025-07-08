# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, TYPE_CHECKING

from PyQt6.QtCore import QObject, pyqtProperty

from cura.API.Backups import Backups
from cura.API.ConnectionStatus import ConnectionStatus
from cura.API.Interface import Interface
from cura.API.Account import Account

if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication


class CuraAPI(QObject):
    """The official Cura API that plug-ins can use to interact with Cura.

    Python does not technically prevent talking to other classes as well, but this API provides a version-safe
    interface with proper deprecation warnings etc. Usage of any other methods than the ones provided in this API can
    cause plug-ins to be unstable.
    """


    # For now we use the same API version to be consistent.
    __instance = None  # type: "CuraAPI"
    _application = None  # type: CuraApplication

    #   This is done to ensure that the first time an instance is created, it's forced that the application is set.
    #   The main reason for this is that we want to prevent consumers of API to have a dependency on CuraApplication.
    #   Since the API is intended to be used by plugins, the cura application should have already created this.
    def __new__(cls, application: Optional["CuraApplication"] = None):
        if cls.__instance is not None:
            raise RuntimeError("Tried to create singleton '{class_name}' more than once.".format(class_name=CuraAPI.__name__))
        if application is None:
            raise RuntimeError("Upon first time creation, the application must be set.")
        instance = super(CuraAPI, cls).__new__(cls)
        cls._application = application
        return instance

    def __init__(self, application: Optional["CuraApplication"] = None) -> None:
        super().__init__(parent=CuraAPI._application)
        CuraAPI.__instance = self

        self._account = Account(self._application)

        self._backups = Backups(self._application)

        self._connectionStatus = ConnectionStatus()

        # Interface API
        self._interface = Interface(self._application)

    def initialize(self) -> None:
        self._account.initialize()

    @pyqtProperty(QObject, constant=True)
    def account(self) -> "Account":
        """Accounts API"""

        return self._account

    @pyqtProperty(QObject, constant=True)
    def connectionStatus(self) -> "ConnectionStatus":
        return self._connectionStatus

    @property
    def backups(self) -> "Backups":
        """Backups API"""

        return self._backups

    @property
    def interface(self) -> "Interface":
        """Interface API"""

        return self._interface
