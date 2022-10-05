from UM.Extension import Extension
from PyQt6.QtQml import qmlRegisterSingletonType

from .AuthService import AuthService
from .PrintersManager import PrintersManager
from UM.Logger import Logger

class ApiPlugin(Extension):
    def __init__(self) -> None:
        Logger.info(f"API Extension init")

        super().__init__()
        self._authentication_service = None
        self._printers_manager = PrintersManager.getInstance()
        
        Logger.info(f"API Extension otra linea")

        #qmlRegisterSingletonType(AuthService, "Cura", 1, 1, self.getAuthenticationService, "AuthenticationService")
        qmlRegisterSingletonType(PrintersManager, "Cura", 1, 1, self.getPrintersManager, "PrintersManagerService")


    def getAuthenticationService(self, *args):
        if self._authentication_service is None:
            self._authentication_service = AuthService.getInstance()
            self._authentication_service.startApi()
        return self._authentication_service

    def getPrintersManager(self, *args):
        if self._printers_manager is None:
            self._printers_manager = PrintersManager.getInstance()
        return self._printers_manager

    

