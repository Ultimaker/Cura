from time import time
from typing import Callable, List, Optional

from PyQt6.QtCore import QObject, pyqtSlot
from PyQt6.QtNetwork import QNetworkReply

from UM import i18nCatalog
from UM.Logger import Logger
from UM.FileHandler.FileHandler import FileHandler
from UM.Resources import Resources
from UM.Scene.SceneNode import SceneNode

from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.NetworkedPrinterOutputDevice import AuthState
from cura.PrinterOutput.PrinterOutputDevice import ConnectionType
from .CloudApiClient import CloudApiClient
from ..Models.Http.CloudClusterWithConfigResponse import CloudClusterWithConfigResponse
from ..UltimakerNetworkedPrinterOutputDevice import UltimakerNetworkedPrinterOutputDevice

I18N_CATALOG = i18nCatalog("cura")


class AbstractCloudOutputDevice(UltimakerNetworkedPrinterOutputDevice):
    API_CHECK_INTERVAL = 10.0  # seconds

    def __init__(self, api_client: CloudApiClient, printer_type: str, request_write_callback: Callable, refresh_callback: Callable, parent: QObject = None) -> None:

        self._api = api_client
        properties = {b"printer_type": printer_type.encode()}
        super().__init__(
            device_id=f"ABSTRACT_{printer_type}",
            address="",
            connection_type=ConnectionType.CloudConnection,
            properties=properties,
            parent=parent
        )

        self._on_print_dialog: Optional[QObject] = None
        self._nodes: List[SceneNode] = None
        self._request_write_callback = request_write_callback
        self._refresh_callback = refresh_callback

        self._setInterfaceElements()

    def connect(self) -> None:
        """Connects this device."""

        if self.isConnected():
            return
        Logger.log("i", "Attempting to connect AbstractCloudOutputDevice %s", self.key)
        super().connect()

        self._update()

    def disconnect(self) -> None:
        """Disconnects the device"""

        if not self.isConnected():
            return
        super().disconnect()

    def _update(self) -> None:
        """Called when the network data should be updated."""

        super()._update()
        if time() - self._time_of_last_request < self.API_CHECK_INTERVAL:
            return  # avoid calling the cloud too often
        self._time_of_last_request = time()
        if self._api.account.isLoggedIn:
            self.setAuthenticationState(AuthState.Authenticated)
            self._last_request_time = time()
            self._api.getClustersByMachineType(self.printerType, self._onCompleted, self._onError)
        else:
            self.setAuthenticationState(AuthState.NotAuthenticated)

    def _setInterfaceElements(self) -> None:
        """Set all the interface elements and texts for this output device."""

        self.setPriority(2)  # Make sure we end up below the local networking and above 'save to file'.
        self.setShortDescription(I18N_CATALOG.i18nc("@action:button", "Print via cloud"))
        self.setDescription(I18N_CATALOG.i18nc("@properties:tooltip", "Print via cloud"))
        self.setConnectionText(I18N_CATALOG.i18nc("@info:status", "Connected via cloud"))

    def _onCompleted(self, clusters: List[CloudClusterWithConfigResponse]) -> None:
        self._responseReceived()

        all_configurations = []
        for resp in clusters:
            if resp.configuration is not None:
                # Usually when the printer is offline, it doesn't have a configuration...
                all_configurations.append(resp.configuration)
        self._updatePrinters(all_configurations)

    def _onError(self, reply: QNetworkReply, error: QNetworkReply.NetworkError) -> None:
        Logger.log("w", f"Failed to get clusters by machine type: {str(error)}.")

    @pyqtSlot(str)
    def printerSelected(self, unique_id: str):
        # The device that it defers the actual write to isn't hooked up correctly. So we should emit the write signal
        # here.
        self.writeStarted.emit(self)
        self._request_write_callback(unique_id, self._nodes)
        if self._on_print_dialog:
            self._on_print_dialog.close()

    @pyqtSlot()
    def refresh(self):
        self._refresh_callback()
        self._update()

    def _openChoosePrinterDialog(self) -> None:
        if self._on_print_dialog is None:
            qml_path = Resources.getPath(CuraApplication.ResourceTypes.QmlFiles, "Dialogs", "ChoosePrinterDialog.qml")
            self._on_print_dialog = CuraApplication.getInstance().createQmlComponent(qml_path, {})
        if self._on_print_dialog is None:  # Failed to load QML file.
            return
        self._on_print_dialog.setProperty("manager", self)
        self._on_print_dialog.show()

    def requestWrite(self, nodes: List[SceneNode], file_name: Optional[str] = None, limit_mimetypes: bool = False, file_handler: Optional[FileHandler] = None, **kwargs) -> None:
        if not nodes or len(nodes) < 1:
            Logger.log("w", "Nothing to print.")
            return
        self._nodes = nodes
        self._openChoosePrinterDialog()
