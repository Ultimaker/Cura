from time import time
from typing import List

from PyQt6.QtCore import QObject
from PyQt6.QtNetwork import QNetworkReply

from UM import i18nCatalog
from UM.Logger import Logger
from cura.PrinterOutput.NetworkedPrinterOutputDevice import AuthState
from cura.PrinterOutput.PrinterOutputDevice import ConnectionType
from .CloudApiClient import CloudApiClient
from ..Models.Http.CloudClusterResponse import CloudClusterResponse
from ..Models.Http.CloudClusterWithConfigResponse import CloudClusterWithConfigResponse
from ..UltimakerNetworkedPrinterOutputDevice import UltimakerNetworkedPrinterOutputDevice

I18N_CATALOG = i18nCatalog("cura")


class AbstractCloudOutputDevice(UltimakerNetworkedPrinterOutputDevice):
    API_CHECK_INTERVAL = 10.0  # seconds

    def __init__(self, api_client: CloudApiClient, printer_type: str, parent: QObject = None) -> None:

        self._api = api_client
        properties = {
            #b"address": cluster.host_internal_ip.encode() if cluster.host_internal_ip else b"",
           # b"name": cluster.friendly_name.encode() if cluster.friendly_name else b"",
            ##b"firmware_version": cluster.host_version.encode() if cluster.host_version else b"",
            b"printer_type": printer_type.encode()
            #b"cluster_size": str(cluster.printer_count).encode() if cluster.printer_count else b"1"
        }
        super().__init__(
            device_id=f"ABSTRACT_{printer_type}",
            address="",
            connection_type=ConnectionType.CloudConnection,
            properties=properties,
            parent=parent
        )

        self._setInterfaceElements()

    def connect(self) -> None:
        """Connects this device."""

        if self.isConnected():
            return
        Logger.log("i", "Attempting to connect AbstractCloudOutputDevice %s", self.key)
        super().connect()

        #CuraApplication.getInstance().getBackend().backendStateChange.connect(self._onBackendStateChange)
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
        pass
