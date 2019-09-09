# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional, Dict, List, Callable, Any

from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import pyqtSlot, QUrl, pyqtSignal, pyqtProperty
from PyQt5.QtNetwork import QNetworkReply

from UM.FileHandler.FileHandler import FileHandler
from UM.i18n import i18nCatalog
from UM.Scene.SceneNode import SceneNode
from cura.PrinterOutput.NetworkedPrinterOutputDevice import AuthState
from cura.PrinterOutput.PrinterOutputDevice import ConnectionType

from .ClusterApiClient import ClusterApiClient
from .SendMaterialJob import SendMaterialJob
from ..ExportFileJob import ExportFileJob
from ..UltimakerNetworkedPrinterOutputDevice import UltimakerNetworkedPrinterOutputDevice
from ..Messages.PrintJobUploadBlockedMessage import PrintJobUploadBlockedMessage
from ..Messages.PrintJobUploadErrorMessage import PrintJobUploadErrorMessage
from ..Messages.PrintJobUploadSuccessMessage import PrintJobUploadSuccessMessage
from ..Models.Http.ClusterMaterial import ClusterMaterial


I18N_CATALOG = i18nCatalog("cura")


class LocalClusterOutputDevice(UltimakerNetworkedPrinterOutputDevice):

    activeCameraUrlChanged = pyqtSignal()

    def __init__(self, device_id: str, address: str, properties: Dict[bytes, bytes], parent=None) -> None:

        super().__init__(
            device_id=device_id,
            address=address,
            properties=properties,
            connection_type=ConnectionType.NetworkConnection,
            parent=parent
        )

        self._cluster_api = None  # type: Optional[ClusterApiClient]

        # We don't have authentication over local networking, so we're always authenticated.
        self.setAuthenticationState(AuthState.Authenticated)
        self._setInterfaceElements()
        self._active_camera_url = QUrl()  # type: QUrl

    ##  Set all the interface elements and texts for this output device.
    def _setInterfaceElements(self) -> None:
        self.setPriority(3)  # Make sure the output device gets selected above local file output
        self.setShortDescription(I18N_CATALOG.i18nc("@action:button Preceded by 'Ready to'.", "Print over network"))
        self.setDescription(I18N_CATALOG.i18nc("@properties:tooltip", "Print over network"))
        self.setConnectionText(I18N_CATALOG.i18nc("@info:status", "Connected over the network"))

    ## Called when the connection to the cluster changes.
    def connect(self) -> None:
        super().connect()
        self._update()
        self.sendMaterialProfiles()

    @pyqtProperty(QUrl, notify=activeCameraUrlChanged)
    def activeCameraUrl(self) -> QUrl:
        return self._active_camera_url

    @pyqtSlot(QUrl, name="setActiveCameraUrl")
    def setActiveCameraUrl(self, camera_url: QUrl) -> None:
        if self._active_camera_url != camera_url:
            self._active_camera_url = camera_url
            self.activeCameraUrlChanged.emit()

    @pyqtSlot(name="openPrintJobControlPanel")
    def openPrintJobControlPanel(self) -> None:
        QDesktopServices.openUrl(QUrl("http://" + self._address + "/print_jobs"))

    @pyqtSlot(name="openPrinterControlPanel")
    def openPrinterControlPanel(self) -> None:
        QDesktopServices.openUrl(QUrl("http://" + self._address + "/printers"))

    @pyqtSlot(str, name="sendJobToTop")
    def sendJobToTop(self, print_job_uuid: str) -> None:
        self._getApiClient().movePrintJobToTop(print_job_uuid)

    @pyqtSlot(str, name="deleteJobFromQueue")
    def deleteJobFromQueue(self, print_job_uuid: str) -> None:
        self._getApiClient().deletePrintJob(print_job_uuid)

    @pyqtSlot(str, name="forceSendJob")
    def forceSendJob(self, print_job_uuid: str) -> None:
        self._getApiClient().forcePrintJob(print_job_uuid)

    ## Set the remote print job state.
    #  \param print_job_uuid: The UUID of the print job to set the state for.
    #  \param action: The action to undertake ('pause', 'resume', 'abort').
    def setJobState(self, print_job_uuid: str, action: str) -> None:
        self._getApiClient().setPrintJobState(print_job_uuid, action)

    def _update(self) -> None:
        super()._update()
        self._getApiClient().getPrinters(self._updatePrinters)
        self._getApiClient().getPrintJobs(self._updatePrintJobs)
        self._updatePrintJobPreviewImages()

    ## Get a list of materials that are installed on the cluster host.
    def getMaterials(self, on_finished: Callable[[List[ClusterMaterial]], Any]) -> None:
        self._getApiClient().getMaterials(on_finished = on_finished)

    ## Sync the material profiles in Cura with the printer.
    #  This gets called when connecting to a printer as well as when sending a print.
    def sendMaterialProfiles(self) -> None:
        job = SendMaterialJob(device = self)
        job.run()

    ## Send a print job to the cluster.
    def requestWrite(self, nodes: List[SceneNode], file_name: Optional[str] = None, limit_mimetypes: bool = False,
                     file_handler: Optional[FileHandler] = None, filter_by_machine: bool = False, **kwargs) -> None:

        # Show an error message if we're already sending a job.
        if self._progress.visible:
            PrintJobUploadBlockedMessage().show()
            return

        self.writeStarted.emit(self)

        # Export the scene to the correct file type.
        job = ExportFileJob(file_handler=file_handler, nodes=nodes, firmware_version=self.firmwareVersion)
        job.finished.connect(self._onPrintJobCreated)
        job.start()

    ## Handler for when the print job was created locally.
    #  It can now be sent over the network.
    def _onPrintJobCreated(self, job: ExportFileJob) -> None:
        self._progress.show()
        parts = [
            self._createFormPart("name=owner", bytes(self._getUserName(), "utf-8"), "text/plain"),
            self._createFormPart("name=\"file\"; filename=\"%s\"" % job.getFileName(), job.getOutput())
        ]
        # FIXME: move form posting to API client
        self.postFormWithParts("/cluster-api/v1/print_jobs/", parts, on_finished=self._onPrintUploadCompleted,
                               on_progress=self._onPrintJobUploadProgress)

    ## Handler for print job upload progress.
    def _onPrintJobUploadProgress(self, bytes_sent: int, bytes_total: int) -> None:
        percentage = (bytes_sent / bytes_total) if bytes_total else 0
        self._progress.setProgress(percentage * 100)
        self.writeProgress.emit()

    ## Handler for when the print job was fully uploaded to the cluster.
    def _onPrintUploadCompleted(self, _: QNetworkReply) -> None:
        self._progress.hide()
        PrintJobUploadSuccessMessage().show()
        self.writeFinished.emit()

    ## Displays the given message if uploading the mesh has failed
    #  \param message: The message to display.
    def _onUploadError(self, message: str = None) -> None:
        self._progress.hide()
        PrintJobUploadErrorMessage(message).show()
        self.writeError.emit()

    ## Download all the images from the cluster and load their data in the print job models.
    def _updatePrintJobPreviewImages(self):
        for print_job in self._print_jobs:
            if print_job.getPreviewImage() is None:
                self._getApiClient().getPrintJobPreviewImage(print_job.key, print_job.updatePreviewImageData)

    ## Get the API client instance.
    def _getApiClient(self) -> ClusterApiClient:
        if not self._cluster_api:
            self._cluster_api = ClusterApiClient(self.address, on_error=lambda error: print(error))
        return self._cluster_api
