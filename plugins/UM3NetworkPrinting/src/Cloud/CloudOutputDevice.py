# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from time import time
import os
from typing import cast, List, Optional, TYPE_CHECKING

from PyQt5.QtCore import QObject, QUrl, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest  # Parse errors specific to print job uploading.

from UM import i18nCatalog
from UM.Backend.Backend import BackendState
from UM.FileHandler.FileHandler import FileHandler
from UM.Logger import Logger
from UM.Scene.SceneNode import SceneNode
from UM.Version import Version
from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.NetworkedPrinterOutputDevice import AuthState
from cura.PrinterOutput.PrinterOutputDevice import ConnectionType

from .CloudApiClient import CloudApiClient
from ..ExportFileJob import ExportFileJob
from ..UltimakerNetworkedPrinterOutputDevice import UltimakerNetworkedPrinterOutputDevice
from ..Messages.PrintJobUploadBlockedMessage import PrintJobUploadBlockedMessage
from ..Messages.PrintJobUploadErrorMessage import PrintJobUploadErrorMessage
from ..Messages.PrintJobUploadQueueFullMessage import PrintJobUploadQueueFullMessage
from ..Messages.PrintJobUploadSuccessMessage import PrintJobUploadSuccessMessage
from ..Models.Http.CloudClusterResponse import CloudClusterResponse
from ..Models.Http.CloudClusterStatus import CloudClusterStatus
from ..Models.Http.CloudPrintJobUploadRequest import CloudPrintJobUploadRequest
from ..Models.Http.CloudPrintResponse import CloudPrintResponse
from ..Models.Http.CloudPrintJobResponse import CloudPrintJobResponse
from ..Models.Http.ClusterPrinterStatus import ClusterPrinterStatus
from ..Models.Http.ClusterPrintJobStatus import ClusterPrintJobStatus


I18N_CATALOG = i18nCatalog("cura")


class CloudOutputDevice(UltimakerNetworkedPrinterOutputDevice):
    """The cloud output device is a network output device that works remotely but has limited functionality.

    Currently it only supports viewing the printer and print job status and adding a new job to the queue.
    As such, those methods have been implemented here.
    Note that this device represents a single remote cluster, not a list of multiple clusters.
    """

    # The interval with which the remote cluster is checked.
    # We can do this relatively often as this API call is quite fast.
    CHECK_CLUSTER_INTERVAL = 10.0  # seconds

    # Override the network response timeout in seconds after which we consider the device offline.
    # For cloud this needs to be higher because the interval at which we check the status is higher as well.
    NETWORK_RESPONSE_CONSIDER_OFFLINE = 15.0  # seconds

    # The minimum version of firmware that support print job actions over cloud.
    PRINT_JOB_ACTIONS_MIN_VERSION = Version("5.2.12")

    # Notify can only use signals that are defined by the class that they are in, not inherited ones.
    # Therefore we create a private signal used to trigger the printersChanged signal.
    _cloudClusterPrintersChanged = pyqtSignal()

    def __init__(self, api_client: CloudApiClient, cluster: CloudClusterResponse, parent: QObject = None) -> None:
        """Creates a new cloud output device

        :param api_client: The client that will run the API calls
        :param cluster: The device response received from the cloud API.
        :param parent: The optional parent of this output device.
        """

        # The following properties are expected on each networked output device.
        # Because the cloud connection does not off all of these, we manually construct this version here.
        # An example of why this is needed is the selection of the compatible file type when exporting the tool path.
        properties = {
            b"address": cluster.host_internal_ip.encode() if cluster.host_internal_ip else b"",
            b"name": cluster.friendly_name.encode() if cluster.friendly_name else b"",
            b"firmware_version": cluster.host_version.encode() if cluster.host_version else b"",
            b"printer_type": cluster.printer_type.encode() if cluster.printer_type else b"",
            b"cluster_size": str(cluster.printer_count).encode() if cluster.printer_count else b"1"
        }

        super().__init__(
            device_id=cluster.cluster_id,
            address="",
            connection_type=ConnectionType.CloudConnection,
            properties=properties,
            parent=parent
        )

        self._api = api_client
        self._account = api_client.account
        self._cluster = cluster
        self.setAuthenticationState(AuthState.NotAuthenticated)
        self._setInterfaceElements()

        # Trigger the printersChanged signal when the private signal is triggered.
        self.printersChanged.connect(self._cloudClusterPrintersChanged)

        # Keep server string of the last generated time to avoid updating models more than once for the same response
        self._received_printers = None  # type: Optional[List[ClusterPrinterStatus]]
        self._received_print_jobs = None  # type: Optional[List[ClusterPrintJobStatus]]

        # Reference to the uploaded print job / mesh
        # We do this to prevent re-uploading the same file multiple times.
        self._tool_path = None  # type: Optional[bytes]
        self._pre_upload_print_job = None  # type: Optional[CloudPrintJobResponse]
        self._uploaded_print_job = None  # type: Optional[CloudPrintJobResponse]

    def connect(self) -> None:
        """Connects this device."""

        if self.isConnected():
            return
        Logger.log("i", "Attempting to connect to cluster %s", self.key)
        super().connect()

        CuraApplication.getInstance().getBackend().backendStateChange.connect(self._onBackendStateChange)
        self._update()

    def disconnect(self) -> None:
        """Disconnects the device"""

        if not self.isConnected():
            return
        super().disconnect()
        Logger.log("i", "Disconnected from cluster %s", self.key)
        CuraApplication.getInstance().getBackend().backendStateChange.disconnect(self._onBackendStateChange)

    def _onBackendStateChange(self, _: BackendState) -> None:
        """Resets the print job that was uploaded to force a new upload, runs whenever the user re-slices."""

        self._tool_path = None
        self._pre_upload_print_job = None
        self._uploaded_print_job = None

    def matchesNetworkKey(self, network_key: str) -> bool:
        """Checks whether the given network key is found in the cloud's host name"""

        # Typically, a network key looks like "ultimakersystem-aabbccdd0011._ultimaker._tcp.local."
        # the host name should then be "ultimakersystem-aabbccdd0011"
        if network_key.startswith(str(self.clusterData.host_name or "")):
            return True
        # However, for manually added printers, the local IP address is used in lieu of a proper
        # network key, so check for that as well. It is in the format "manual:10.1.10.1".
        if network_key.endswith(str(self.clusterData.host_internal_ip or "")):
            return True
        return False

    def _setInterfaceElements(self) -> None:
        """Set all the interface elements and texts for this output device."""

        self.setPriority(2)  # Make sure we end up below the local networking and above 'save to file'.
        self.setShortDescription(I18N_CATALOG.i18nc("@action:button", "Print via cloud"))
        self.setDescription(I18N_CATALOG.i18nc("@properties:tooltip", "Print via cloud"))
        self.setConnectionText(I18N_CATALOG.i18nc("@info:status", "Connected via cloud"))

    def _update(self) -> None:
        """Called when the network data should be updated."""

        super()._update()
        if time() - self._time_of_last_request < self.CHECK_CLUSTER_INTERVAL:
            return  # avoid calling the cloud too often
        self._time_of_last_request = time()
        if self._account.isLoggedIn:
            self.setAuthenticationState(AuthState.Authenticated)
            self._last_request_time = time()
            self._api.getClusterStatus(self.key, self._onStatusCallFinished)
        else:
            self.setAuthenticationState(AuthState.NotAuthenticated)

    def _onStatusCallFinished(self, status: CloudClusterStatus) -> None:
        """Method called when HTTP request to status endpoint is finished.

        Contains both printers and print jobs statuses in a single response.
        """
        self._responseReceived()
        if status.printers != self._received_printers:
            self._received_printers = status.printers
            self._updatePrinters(status.printers)
        if status.print_jobs != self._received_print_jobs:
            self._received_print_jobs = status.print_jobs
            self._updatePrintJobs(status.print_jobs)

    def requestWrite(self, nodes: List[SceneNode], file_name: Optional[str] = None, limit_mimetypes: bool = False,
                     file_handler: Optional[FileHandler] = None, filter_by_machine: bool = False, **kwargs) -> None:

        """Called when Cura requests an output device to receive a (G-code) file."""

        # Show an error message if we're already sending a job.
        if self._progress.visible:
            PrintJobUploadBlockedMessage().show()
            return
        self._progress.show()

        # Indicate we have started sending a job.
        self.writeStarted.emit(self)

        # The mesh didn't change, let's not upload it to the cloud again.
        # Note that self.writeFinished is called in _onPrintUploadCompleted as well.
        if self._uploaded_print_job:
            Logger.log("i", "Current mesh is already attached to a print-job, immediately request reprint.")
            self._api.requestPrint(self.key, self._uploaded_print_job.job_id, self._onPrintUploadCompleted, self._onPrintUploadSpecificError)
            return

        # Export the scene to the correct file type.
        job = ExportFileJob(file_handler=file_handler, nodes=nodes, firmware_version=self.firmwareVersion)
        job.finished.connect(self._onPrintJobCreated)
        job.start()

    def _onPrintJobCreated(self, job: ExportFileJob) -> None:
        """Handler for when the print job was created locally.

        It can now be sent over the cloud.
        """
        output = job.getOutput()
        self._tool_path = output  # store the tool path to prevent re-uploading when printing the same file again
        file_name = job.getFileName()
        request = CloudPrintJobUploadRequest(
            job_name=os.path.splitext(file_name)[0],
            file_size=len(output),
            content_type=job.getMimeType(),
        )
        self._api.requestUpload(request, self._uploadPrintJob)

    def _uploadPrintJob(self, job_response: CloudPrintJobResponse) -> None:
        """Uploads the mesh when the print job was registered with the cloud API.

        :param job_response: The response received from the cloud API.
        """
        if not self._tool_path:
            return self._onUploadError()
        self._pre_upload_print_job = job_response  # store the last uploaded job to prevent re-upload of the same file
        self._api.uploadToolPath(job_response, self._tool_path, self._onPrintJobUploaded, self._progress.update,
                                 self._onUploadError)

    def _onPrintJobUploaded(self) -> None:
        """
        Requests the print to be sent to the printer when we finished uploading
        the mesh.
        """

        self._progress.update(100)
        print_job = cast(CloudPrintJobResponse, self._pre_upload_print_job)
        if not print_job:  # It's possible that another print job is requested in the meanwhile, which then fails to upload with an error, which sets self._pre_uploaded_print_job to `None`.
            self._pre_upload_print_job = None
            self._uploaded_print_job = None
            Logger.log("w", "Interference from another job uploaded at roughly the same time, not uploading print!")
            return  # Prevent a crash.
        self._api.requestPrint(self.key, print_job.job_id, self._onPrintUploadCompleted, self._onPrintUploadSpecificError)

    def _onPrintUploadCompleted(self, response: CloudPrintResponse) -> None:
        """Shows a message when the upload has succeeded

        :param response: The response from the cloud API.
        """
        self._uploaded_print_job = self._pre_upload_print_job
        self._progress.hide()
        message = PrintJobUploadSuccessMessage()
        message.addAction("monitor print",
                          name=I18N_CATALOG.i18nc("@action:button", "Monitor print"),
                          icon="",
                          description=I18N_CATALOG.i18nc("@action:tooltip", "Track the print in Ultimaker Digital Factory"),
                          button_align=message.ActionButtonAlignment.ALIGN_RIGHT)
        df_url = f"https://digitalfactory.ultimaker.com/app/jobs/{self._cluster.cluster_id}?utm_source=cura&utm_medium=software&utm_campaign=message-printjob-sent"
        message.pyQtActionTriggered.connect(lambda message, action: (QDesktopServices.openUrl(QUrl(df_url)), message.hide()))

        message.show()
        self.writeFinished.emit()

    def _onPrintUploadSpecificError(self, reply: "QNetworkReply", _: "QNetworkReply.NetworkError"):
        """
        Displays a message when an error occurs specific to uploading print job (i.e. queue is full).
        """
        error_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if error_code == 409:
            PrintJobUploadQueueFullMessage().show()
        else:
            PrintJobUploadErrorMessage(I18N_CATALOG.i18nc("@error:send", "Unknown error code when uploading print job: {0}", error_code)).show()

        Logger.log("w", "Upload of print job failed specifically with error code {}".format(error_code))

        self._progress.hide()
        self._pre_upload_print_job = None
        self._uploaded_print_job = None
        self.writeError.emit()

    def _onUploadError(self, message: str = None) -> None:
        """
        Displays the given message if uploading the mesh has failed due to a generic error (i.e. lost connection).
        :param message: The message to display.
        """
        Logger.log("w", "Upload error with message {}".format(message))

        self._progress.hide()
        self._pre_upload_print_job = None
        self._uploaded_print_job = None
        PrintJobUploadErrorMessage(message).show()
        self.writeError.emit()

    @pyqtProperty(bool, notify=_cloudClusterPrintersChanged)
    def supportsPrintJobActions(self) -> bool:
        """Whether the printer that this output device represents supports print job actions via the cloud."""

        if not self._printers:
            return False
        version_number = self.printers[0].firmwareVersion.split(".")
        firmware_version = Version([version_number[0], version_number[1], version_number[2]])
        return firmware_version >= self.PRINT_JOB_ACTIONS_MIN_VERSION

    @pyqtProperty(bool, constant = True)
    def supportsPrintJobQueue(self) -> bool:
        """Gets whether the printer supports a queue"""

        return "queue" in self._cluster.capabilities if self._cluster.capabilities else True

    def setJobState(self, print_job_uuid: str, state: str) -> None:
        """Set the remote print job state."""

        self._api.doPrintJobAction(self._cluster.cluster_id, print_job_uuid, state)

    @pyqtSlot(str, name="sendJobToTop")
    def sendJobToTop(self, print_job_uuid: str) -> None:
        self._api.doPrintJobAction(self._cluster.cluster_id, print_job_uuid, "move",
                                   {"list": "queued", "to_position": 0})

    @pyqtSlot(str, name="deleteJobFromQueue")
    def deleteJobFromQueue(self, print_job_uuid: str) -> None:
        self._api.doPrintJobAction(self._cluster.cluster_id, print_job_uuid, "remove")

    @pyqtSlot(str, name="forceSendJob")
    def forceSendJob(self, print_job_uuid: str) -> None:
        self._api.doPrintJobAction(self._cluster.cluster_id, print_job_uuid, "force")

    @pyqtSlot(name="openPrintJobControlPanel")
    def openPrintJobControlPanel(self) -> None:
        QDesktopServices.openUrl(QUrl(self.clusterCloudUrl + "?utm_source=cura&utm_medium=software&utm_campaign=monitor-manage-browser"))

    @pyqtSlot(name="openPrinterControlPanel")
    def openPrinterControlPanel(self) -> None:
        QDesktopServices.openUrl(QUrl(self.clusterCloudUrl + "?utm_source=cura&utm_medium=software&utm_campaign=monitor-manage-printer"))

    @property
    def clusterData(self) -> CloudClusterResponse:
        """Gets the cluster response from which this device was created."""

        return self._cluster

    @clusterData.setter
    def clusterData(self, value: CloudClusterResponse) -> None:
        """Updates the cluster data from the cloud."""

        self._cluster = value

    @property
    def clusterCloudUrl(self) -> str:
        """Gets the URL on which to monitor the cluster via the cloud."""

        root_url_prefix = "-staging" if self._account.is_staging else ""
        return "https://digitalfactory{}.ultimaker.com/app/jobs/{}".format(root_url_prefix, self.clusterData.cluster_id)
