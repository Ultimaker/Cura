from UM.Extension import Extension
from PyQt6.QtQml import qmlRegisterSingletonType

from .extensions.api.AuthService import AuthService
from .extensions.api.PrintersManager import PrintersManager

class BCN3DOFF(Extension):
    def __init__(self) -> None:

        super().__init__()
        super().__init__()
        self._authentication_service = None
        self._printers_manager = None
        self._printers_manager = PrintersManager.getInstance()

        qmlRegisterSingletonType(AuthService, "Cura", 1, 1, "AuthenticationService", self.getAuthenticationService,)
        qmlRegisterSingletonType(PrintersManager, "Cura", 1, 1, "PrintersManagerService", self.getPrintersManager, )

        
    def getAuthenticationService(self, *args):
        if self._authentication_service is None:
            self._authentication_service = AuthService.getInstance()
            self._authentication_service.startApi()
        return self._authentication_service

    def getPrintersManager(self, *args):
        if self._printers_manager is None:
            self._printers_manager = PrintersManager.getInstance()
        return self._printers_manager

    

