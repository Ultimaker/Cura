# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import os
from typing import Optional, Dict, List, Callable, Any

from time import time

from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import pyqtSlot, QUrl, pyqtSignal, pyqtProperty, QObject
from PyQt6.QtNetwork import QNetworkReply

from UM.FileHandler.FileHandler import FileHandler
from UM.Version import Version
from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Scene.SceneNode import SceneNode
from cura.CuraApplication import CuraApplication
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

    CHECK_CLUSTER_INTERVAL = 10.0  # seconds

    def __init__(self, device_id: str, address: str, properties: Dict[bytes, bytes], parent=None) -> None:

        super().__init__(
            device_id=device_id,
            address=address,
            properties=properties,
            connection_type=ConnectionType.NetworkConnection,
            parent=parent
        )
        self._timeout_time = 30
        self._cluster_api = None  # type: Optional[ClusterApiClient]
        self._active_exported_job = None  # type: Optional[ExportFileJob]
        self._printer_select_dialog = None  # type: Optional[QObject]

        # We don't have authentication over local networking, so we're always authenticated.
        self.setAuthenticationState(AuthState.Authenticated)
        self._setInterfaceElements()
        self._active_camera_url = QUrl()  # type: QUrl

    def _setInterfaceElements(self) -> None:
        """Set all the interface elements and texts for this output device."""

        self.setPriority(3)  # Make sure the output device gets selected above local file output
        self.setShortDescription(I18N_CATALOG.i18nc("@action:button Preceded by 'Ready to'.", "Print over network"))
        self.setDescription(I18N_CATALOG.i18nc("@properties:tooltip", "Print over network"))
        self.setConnectionText(I18N_CATALOG.i18nc("@info:status", "Connected over the network"))

    def connect(self) -> None:
        """Called when the connection to the cluster changes."""

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
        if Version(self.firmwareVersion) >= Version("7.0.2"):
            QDesktopServices.openUrl(QUrl("http://" + self._address + "/print_jobs"))
        else:
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

    def setJobState(self, print_job_uuid: str, action: str) -> None:
        """Set the remote print job state.

        :param print_job_uuid: The UUID of the print job to set the state for.
        :param action: The action to undertake ('pause', 'resume', 'abort').
        """

        self._getApiClient().setPrintJobState(print_job_uuid, action)

    def _update(self) -> None:
        super()._update()
        if time() - self._time_of_last_request < self.CHECK_CLUSTER_INTERVAL:
            return  # avoid calling the cluster too often
        self._getApiClient().getPrinters(self._updatePrinters)
        self._getApiClient().getPrintJobs(self._updatePrintJobs)
        self._updatePrintJobPreviewImages()

    def getMaterials(self, on_finished: Callable[[List[ClusterMaterial]], Any]) -> None:
        """Get a list of materials that are installed on the cluster host."""

        self._getApiClient().getMaterials(on_finished = on_finished)

    def sendMaterialProfiles(self) -> None:
        """Sync the material profiles in Cura with the printer.

        This gets called when connecting to a printer as well as when sending a print.
        """
        job = SendMaterialJob(device = self)
        job.run()

    def requestWrite(self, nodes: List[SceneNode], file_name: Optional[str] = None, limit_mimetypes: bool = False,
                     file_handler: Optional[FileHandler] = None, filter_by_machine: bool = False, **kwargs) -> None:
        """Send a print job to the cluster."""

        # Show an error message if we're already sending a job.
        if self._progress.visible:
            PrintJobUploadBlockedMessage().show()
            return

        self.writeStarted.emit(self)

        # Export the scene to the correct file type.
        job = ExportFileJob(
            file_handler=file_handler,
            nodes=nodes,
            firmware_version=self.firmwareVersion,
            print_type=self.printerType,
        )
        job.finished.connect(self._onPrintJobCreated)
        job.start()

    @pyqtSlot(str, name="selectTargetPrinter")
    def selectTargetPrinter(self, unique_name: str = "") -> None:
        """Allows the user to choose a printer to print with from the printer selection dialogue.

        :param unique_name: The unique name of the printer to target.
        """
        self._startPrintJobUpload(unique_name if unique_name != "" else None)

    def _onPrintJobCreated(self, job: ExportFileJob) -> None:
        """Handler for when the print job was created locally.

        It can now be sent over the network.
        """

        self._active_exported_job = job
        # TODO: add preference to enable/disable this feature?
        if self.clusterSize > 1:
            self._showPrinterSelectionDialog()  # self._startPrintJobUpload will be triggered from this dialog
            return
        self._startPrintJobUpload()

    def _showPrinterSelectionDialog(self) -> None:
        """Shows a dialog allowing the user to select which printer in a group to send a job to."""

        if not self._printer_select_dialog:
            plugin_path = CuraApplication.getInstance().getPluginRegistry().getPluginPath("UM3NetworkPrinting") or ""
            path = os.path.join(plugin_path, "resources", "qml", "PrintWindow.qml")
            self._printer_select_dialog = CuraApplication.getInstance().createQmlComponent(path, {"OutputDevice": self})
        if self._printer_select_dialog is not None:
            self._printer_select_dialog.show()

    def _startPrintJobUpload(self, unique_name: str = None) -> None:
        """Upload the print job to the group."""

        if not self._active_exported_job:
            Logger.log("e", "No active exported job to upload!")
            return
        self._progress.show()
        parts = [
            self._createFormPart("name=owner", bytes(self._getUserName(), "utf-8"), "text/plain"),
            self._createFormPart("name=\"file\"; filename=\"%s\"" % self._active_exported_job.getFileName(),
                                 self._active_exported_job.getOutput())
        ]
        # If a specific printer was selected we include the name in the request.
        # FIXME: Connect should allow the printer UUID here instead of the 'unique_name'.
        if unique_name is not None:
            parts.append(self._createFormPart("name=require_printer_name", bytes(unique_name, "utf-8"), "text/plain"))
        # FIXME: move form posting to API client
        self.postFormWithParts("/cluster-api/v1/print_jobs/", parts, on_finished=self._onPrintUploadCompleted,
                               on_progress=self._onPrintJobUploadProgress)
        self._active_exported_job = None

    def _onPrintJobUploadProgress(self, bytes_sent: int, bytes_total: int) -> None:
        """Handler for print job upload progress."""

        percentage = (bytes_sent / bytes_total) if bytes_total else 0
        self._progress.setProgress(percentage * 100)
        self.writeProgress.emit()

    def _onPrintUploadCompleted(self, _: QNetworkReply) -> None:
        """Handler for when the print job was fully uploaded to the cluster."""

        self._progress.hide()
        PrintJobUploadSuccessMessage().show()
        self.writeFinished.emit()

    def _onUploadError(self, message: str = None) -> None:
        """Displays the given message if uploading the mesh has failed

        :param message: The message to display.
        """

        self._progress.hide()
        PrintJobUploadErrorMessage(message).show()
        self.writeError.emit()

    def _updatePrintJobPreviewImages(self):
        """Download all the images from the cluster and load their data in the print job models."""

        for print_job in self._print_jobs:
            if print_job.getPreviewImage() is None:
                self._getApiClient().getPrintJobPreviewImage(print_job.key, print_job.updatePreviewImageData)

    def _getApiClient(self) -> ClusterApiClient:
        """Get the API client instance."""

        if not self._cluster_api:
            self._cluster_api = ClusterApiClient(self.address, on_error = lambda error: Logger.log("e", str(error)))
        return self._cluster_api
