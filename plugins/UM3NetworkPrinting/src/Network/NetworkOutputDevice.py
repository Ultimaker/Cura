# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional, Dict, List, Any

from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import pyqtSlot, QUrl, pyqtSignal, pyqtProperty
from PyQt5.QtNetwork import QNetworkReply

from UM.FileHandler.FileHandler import FileHandler
from UM.FileHandler.WriteFileJob import WriteFileJob
from UM.Logger import Logger
from UM.Message import Message
from UM.i18n import i18nCatalog
from UM.Scene.SceneNode import SceneNode
from cura.PrinterOutput.NetworkedPrinterOutputDevice import AuthState
from cura.PrinterOutput.PrinterOutputDevice import ConnectionType

from .ClusterApiClient import ClusterApiClient
from ..ExportFileJob import ExportFileJob
from ..SendMaterialJob import SendMaterialJob
from ..UltimakerNetworkedPrinterOutputDevice import UltimakerNetworkedPrinterOutputDevice


I18N_CATALOG = i18nCatalog("cura")


class NetworkOutputDevice(UltimakerNetworkedPrinterOutputDevice):

    activeCameraUrlChanged = pyqtSignal()

    def __init__(self, device_id: str, address: str, properties: Dict[bytes, bytes], parent=None) -> None:

        super().__init__(
            device_id=device_id,
            address=address,
            properties=properties,
            connection_type=ConnectionType.NetworkConnection,
            parent=parent
        )

        # API client for making requests to the print cluster.
        self._cluster_api = ClusterApiClient(address, on_error=self._onNetworkError)
        # We don't have authentication over local networking, so we're always authenticated.
        self.setAuthenticationState(AuthState.Authenticated)
        self._setInterfaceElements()
        self._active_camera_url = QUrl()  # type: QUrl

    ##  Set all the interface elements and texts for this output device.
    def _setInterfaceElements(self) -> None:
        self.setPriority(3)  # Make sure the output device gets selected above local file output
        self.setName(self._id)
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
        self._cluster_api.movePrintJobToTop(print_job_uuid)

    @pyqtSlot(str, name="deleteJobFromQueue")
    def deleteJobFromQueue(self, print_job_uuid: str) -> None:
        self._cluster_api.deletePrintJob(print_job_uuid)

    @pyqtSlot(str, name="forceSendJob")
    def forceSendJob(self, print_job_uuid: str) -> None:
        pass  # TODO

    ## Set the remote print job state.
    #  \param print_job_uuid: The UUID of the print job to set the state for.
    #  \param action: The action to undertake ('pause', 'resume', 'abort').
    def setJobState(self, print_job_uuid: str, action: str) -> None:
        self._cluster_api.setPrintJobState(print_job_uuid, action)

    ## Handle network errors.
    @staticmethod
    def _onNetworkError(errors: Dict[str, Any]):
        Logger.log("w", str(errors))

    def _update(self) -> None:
        super()._update()
        self._cluster_api.getPrinters(self._updatePrinters)
        self._cluster_api.getPrintJobs(self._updatePrintJobs)
        # for print_job in self._print_jobs:
        #     if print_job.getPreviewImage() is None:
        #         self.get("print_jobs/{uuid}/preview_image".format(uuid=print_job.key), on_finished=self._onGetPreviewImageFinished)

    ## Sync the material profiles in Cura with the printer.
    #  This gets called when connecting to a printer as well as when sending a print.
    def sendMaterialProfiles(self) -> None:
        job = SendMaterialJob(device=self)
        job.run()

    # ## Callback for when preview image was downloaded from cluster.
    # def _onGetPreviewImageFinished(self, reply: QNetworkReply) -> None:
    #     reply_url = reply.url().toString()
    #
    #     uuid = reply_url[reply_url.find("print_jobs/")+len("print_jobs/"):reply_url.rfind("/preview_image")]
    #
    #     print_job = findByKey(self._print_jobs, uuid)
    #     if print_job:
    #         image = QImage()
    #         image.loadFromData(reply.readAll())
    #         print_job.updatePreviewImage(image)

    ## Send a print job to the cluster.
    def requestWrite(self, nodes: List[SceneNode], file_name: Optional[str] = None, limit_mimetypes: bool = False,
                     file_handler: Optional[FileHandler] = None, filter_by_machine: bool = False, **kwargs) -> None:

        # Show an error message if we're already sending a job.
        if self._progress.visible:
            message = Message(
                text=I18N_CATALOG.i18nc("@info:status", "Please wait until the current job has been sent."),
                title=I18N_CATALOG.i18nc("@info:title", "Print error"),
                lifetime=10
            )
            message.show()
            return

        self.writeStarted.emit(self)

        # Make sure the printer is aware of all new materials as the new print job might contain one.
        self.sendMaterialProfiles()

        # Export the scene to the correct file type.
        job = ExportFileJob(file_handler=file_handler, nodes=nodes, firmware_version=self.firmwareVersion)
        job.finished.connect(self._onPrintJobCreated)
        job.start()

    ## Handler for when the print job was created locally.
    #  It can now be sent over the network.
    def _onPrintJobCreated(self, job: WriteFileJob) -> None:
        self._progress.show()
        parts = [
            self._createFormPart("name=owner", bytes(self._getUserName(), "utf-8"), "text/plain"),
            self._createFormPart("name=\"file\"; filename=\"%s\"" % job.getFileName(), job.getOutput())
        ]
        self.postFormWithParts("/cluster-api/v1/print_jobs/", parts, on_finished=self._onPrintUploadCompleted,
                               on_progress=self._onPrintJobUploadProgress)

    ## Handler for print job upload progress.
    def _onPrintJobUploadProgress(self, bytes_sent: int, bytes_total: int) -> None:
        percentage = (bytes_sent / bytes_total) if bytes_total else 0
        self._progress.setProgress(percentage * 100)
        self.writeProgress.emit()

    ## Handler for when the print job was fully uploaded to the cluster.
    def _onPrintUploadCompleted(self, reply: QNetworkReply) -> None:
        self._progress.hide()
        Message(
            text=I18N_CATALOG.i18nc("@info:status", "Print job was successfully sent to the printer."),
            title=I18N_CATALOG.i18nc("@info:title", "Data Sent"),
            lifetime=5
        ).show()
        self.writeFinished.emit()

    ## Displays the given message if uploading the mesh has failed
    #  \param message: The message to display.
    def _onUploadError(self, message: str = None) -> None:
        self._progress.hide()
        Message(
            text=message or I18N_CATALOG.i18nc("@info:text", "Could not upload the data to the printer."),
            title=I18N_CATALOG.i18nc("@info:title", "Network error"),
            lifetime=10
        ).show()
        self.writeError.emit()
