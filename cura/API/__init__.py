# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional, TYPE_CHECKING

from PyQt5.QtCore import QObject, pyqtProperty

from UM.PluginRegistry import PluginRegistry
from cura.API.Backups import Backups
from cura.API.Interface import Interface
from cura.API.Account import Account

if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication


##  The official Cura API that plug-ins can use to interact with Cura.
#
#   Python does not technically prevent talking to other classes as well, but
#   this API provides a version-safe interface with proper deprecation warnings
#   etc. Usage of any other methods than the ones provided in this API can cause
#   plug-ins to be unstable.
class CuraAPI(QObject):

    # For now we use the same API version to be consistent.
    VERSION = PluginRegistry.APIVersion

    def __init__(self, application: "CuraApplication") -> None:
        super().__init__(parent = application)
        self._application = application

        # Accounts API
        self._account = Account(self._application)

        # Backups API
        self._backups = Backups(self._application)

        # Interface API
        self._interface = Interface(self._application)

    def initialize(self) -> None:
        self._account.initialize()

    @pyqtProperty(QObject, constant = True)
    def account(self) -> "Account":
        return self._account

    @property
    def backups(self) -> "Backups":
        return self._backups

    @property
    def interface(self) -> "Interface":
        return self._interface