# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import os

from time import time
from typing import Dict, List, Optional, Set, cast

from PyQt5.QtCore import QObject, QUrl, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QDesktopServices

from UM import i18nCatalog
from UM.Backend.Backend import BackendState
from UM.FileHandler.FileHandler import FileHandler
from UM.Logger import Logger
from UM.Message import Message
from UM.PluginRegistry import PluginRegistry
from UM.Qt.Duration import Duration, DurationFormat
from UM.Scene.SceneNode import SceneNode
from UM.Version import Version

from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.NetworkedPrinterOutputDevice import AuthState, NetworkedPrinterOutputDevice
from cura.PrinterOutput.Models.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.PrinterOutputDevice import ConnectionType

from .CloudOutputController import CloudOutputController
from ..MeshFormatHandler import MeshFormatHandler
from ..UM3PrintJobOutputModel import UM3PrintJobOutputModel
from .CloudProgressMessage import CloudProgressMessage
from .CloudApiClient import CloudApiClient
from .Models.CloudClusterResponse import CloudClusterResponse
from .Models.CloudClusterStatus import CloudClusterStatus
from .Models.CloudPrintJobUploadRequest import CloudPrintJobUploadRequest
from .Models.CloudPrintResponse import CloudPrintResponse
from .Models.CloudPrintJobResponse import CloudPrintJobResponse
from .Models.CloudClusterPrinterStatus import CloudClusterPrinterStatus
from .Models.CloudClusterPrintJobStatus import CloudClusterPrintJobStatus
from .Utils import findChanges, formatDateCompleted, formatTimeCompleted


I18N_CATALOG = i18nCatalog("cura")


##  The cloud output device is a network output device that works remotely but has limited functionality.
#   Currently it only supports viewing the printer and print job status and adding a new job to the queue.
#   As such, those methods have been implemented here.
#   Note that this device represents a single remote cluster, not a list of multiple clusters.
class CloudOutputDevice(NetworkedPrinterOutputDevice):

    # The interval with which the remote clusters are checked
    CHECK_CLUSTER_INTERVAL = 10.0  # seconds

    # The minimum version of firmware that support print job actions over cloud.
    PRINT_JOB_ACTIONS_MIN_VERSION = Version("5.3.0")

    # Signal triggered when the print jobs in the queue were changed.
    printJobsChanged = pyqtSignal()

    # Signal triggered when the selected printer in the UI should be changed.
    activePrinterChanged = pyqtSignal()

    # Notify can only use signals that are defined by the class that they are in, not inherited ones.
    # Therefore we create a private signal used to trigger the printersChanged signal.
    _clusterPrintersChanged = pyqtSignal()

    ## Creates a new cloud output device
    #  \param api_client: The client that will run the API calls
    #  \param cluster: The device response received from the cloud API.
    #  \param parent: The optional parent of this output device.
    def __init__(self, api_client: CloudApiClient, cluster: CloudClusterResponse, parent: QObject = None) -> None:

        # The following properties are expected on each networked output device.
        # Because the cloud connection does not off all of these, we manually construct this version here.
        # An example of why this is needed is the selection of the compatible file type when exporting the tool path.
        properties = {
            b"address": cluster.host_internal_ip.encode() if cluster.host_internal_ip else b"",
            b"name": cluster.friendly_name.encode() if cluster.friendly_name else b"",
            b"firmware_version": cluster.host_version.encode() if cluster.host_version else b"",
            b"printer_type": cluster.printer_type.encode() if cluster.printer_type else b"",
            b"cluster_size": b"1"  # cloud devices are always clusters of at least one
        }

        super().__init__(device_id = cluster.cluster_id, address = "",
                         connection_type = ConnectionType.CloudConnection, properties = properties, parent = parent)
        self._api = api_client
        self._cluster = cluster

        self._setInterfaceElements()

        self._account = api_client.account

        # We use the Cura Connect monitor tab to get most functionality right away.
        if PluginRegistry.getInstance() is not None:
            plugin_path = PluginRegistry.getInstance().getPluginPath("UM3NetworkPrinting")
            if plugin_path is None:
                Logger.log("e", "Cloud not find plugin path for plugin UM3NetworkPrnting")
                raise RuntimeError("Cloud not find plugin path for plugin UM3NetworkPrnting")
            self._monitor_view_qml_path = os.path.join(plugin_path, "resources", "qml", "MonitorStage.qml")

        # Trigger the printersChanged signal when the private signal is triggered.
        self.printersChanged.connect(self._clusterPrintersChanged)

        # We keep track of which printer is visible in the monitor page.
        self._active_printer = None  # type: Optional[PrinterOutputModel]

        # Properties to populate later on with received cloud data.
        self._print_jobs = []  # type: List[UM3PrintJobOutputModel]
        self._number_of_extruders = 2  # All networked printers are dual-extrusion Ultimaker machines.

        # We only allow a single upload at a time.
        self._progress = CloudProgressMessage()

        # Keep server string of the last generated time to avoid updating models more than once for the same response
        self._received_printers = None  # type: Optional[List[CloudClusterPrinterStatus]]
        self._received_print_jobs = None  # type: Optional[List[CloudClusterPrintJobStatus]]

        # A set of the user's job IDs that have finished
        self._finished_jobs = set()  # type: Set[str]

        # Reference to the uploaded print job / mesh
        self._tool_path = None  # type: Optional[bytes]
        self._uploaded_print_job = None  # type: Optional[CloudPrintJobResponse]

    ## Connects this device.
    def connect(self) -> None:
        if self.isConnected():
            return
        super().connect()
        Logger.log("i", "Connected to cluster %s", self.key)
        CuraApplication.getInstance().getBackend().backendStateChange.connect(self._onBackendStateChange)

    ## Disconnects the device
    def disconnect(self) -> None:
        super().disconnect()
        Logger.log("i", "Disconnected from cluster %s", self.key)
        CuraApplication.getInstance().getBackend().backendStateChange.disconnect(self._onBackendStateChange)

    ## Resets the print job that was uploaded to force a new upload, runs whenever the user re-slices.
    def _onBackendStateChange(self, _: BackendState) -> None:
        self._tool_path = None
        self._uploaded_print_job = None

    ## Gets the cluster response from which this device was created.
    @property
    def clusterData(self) -> CloudClusterResponse:
        return self._cluster

    ## Updates the cluster data from the cloud.
    @clusterData.setter
    def clusterData(self, value: CloudClusterResponse) -> None:
        self._cluster = value

    ## Checks whether the given network key is found in the cloud's host name
    def matchesNetworkKey(self, network_key: str) -> bool:
        # Typically, a network key looks like "ultimakersystem-aabbccdd0011._ultimaker._tcp.local."
        # the host name should then be "ultimakersystem-aabbccdd0011"
        if network_key.startswith(self.clusterData.host_name):
            return True

        # However, for manually added printers, the local IP address is used in lieu of a proper
        # network key, so check for that as well
        if self.clusterData.host_internal_ip is not None and network_key.find(self.clusterData.host_internal_ip):
            return True

        return False

    ##  Set all the interface elements and texts for this output device.
    def _setInterfaceElements(self) -> None:
        self.setPriority(2)  # Make sure we end up below the local networking and above 'save to file'
        self.setName(self._id)
        self.setShortDescription(I18N_CATALOG.i18nc("@action:button", "Print via Cloud"))
        self.setDescription(I18N_CATALOG.i18nc("@properties:tooltip", "Print via Cloud"))
        self.setConnectionText(I18N_CATALOG.i18nc("@info:status", "Connected via Cloud"))

    ##  Called when Cura requests an output device to receive a (G-code) file.
    def requestWrite(self, nodes: List[SceneNode], file_name: Optional[str] = None, limit_mimetypes: bool = False,
                     file_handler: Optional[FileHandler] = None, **kwargs: str) -> None:

        # Show an error message if we're already sending a job.
        if self._progress.visible:
            message = Message(
                text = I18N_CATALOG.i18nc("@info:status", "Sending new jobs (temporarily) blocked, still sending the previous print job."),
                title = I18N_CATALOG.i18nc("@info:title", "Cloud error"),
                lifetime = 10
            )
            message.show()
            return

        if self._uploaded_print_job:
            # The mesh didn't change, let's not upload it again
            self._api.requestPrint(self.key, self._uploaded_print_job.job_id, self._onPrintUploadCompleted)
            return

        # Indicate we have started sending a job.
        self.writeStarted.emit(self)

        mesh_format = MeshFormatHandler(file_handler, self.firmwareVersion)
        if not mesh_format.is_valid:
            Logger.log("e", "Missing file or mesh writer!")
            return self._onUploadError(I18N_CATALOG.i18nc("@info:status", "Could not export print job."))

        mesh = mesh_format.getBytes(nodes)

        self._tool_path = mesh
        request = CloudPrintJobUploadRequest(
            job_name = file_name or mesh_format.file_extension,
            file_size = len(mesh),
            content_type = mesh_format.mime_type,
        )
        self._api.requestUpload(request, self._onPrintJobCreated)

    ##  Called when the network data should be updated.
    def _update(self) -> None:
        super()._update()
        if self._last_request_time and time() - self._last_request_time < self.CHECK_CLUSTER_INTERVAL:
            return  # Avoid calling the cloud too often

        Logger.log("d", "Updating: %s - %s >= %s", time(), self._last_request_time, self.CHECK_CLUSTER_INTERVAL)
        if self._account.isLoggedIn:
            self.setAuthenticationState(AuthState.Authenticated)
            self._last_request_time = time()
            self._api.getClusterStatus(self.key, self._onStatusCallFinished)
        else:
            self.setAuthenticationState(AuthState.NotAuthenticated)

    ##  Method called when HTTP request to status endpoint is finished.
    #   Contains both printers and print jobs statuses in a single response.
    def _onStatusCallFinished(self, status: CloudClusterStatus) -> None:
        # Update all data from the cluster.
        self._last_response_time = time()
        if self._received_printers != status.printers:
            self._received_printers = status.printers
            self._updatePrinters(status.printers)

        if status.print_jobs != self._received_print_jobs:
            self._received_print_jobs = status.print_jobs
            self._updatePrintJobs(status.print_jobs)

    ## Updates the local list of printers with the list received from the cloud.
    #  \param jobs: The printers received from the cloud.
    def _updatePrinters(self, printers: List[CloudClusterPrinterStatus]) -> None:
        previous = {p.key: p for p in self._printers}  # type: Dict[str, PrinterOutputModel]
        received = {p.uuid: p for p in printers}  # type: Dict[str, CloudClusterPrinterStatus]
        removed_printers, added_printers, updated_printers = findChanges(previous, received)

        for removed_printer in removed_printers:
            if self._active_printer == removed_printer:
                self.setActivePrinter(None)
            self._printers.remove(removed_printer)

        for added_printer in added_printers:
            self._printers.append(added_printer.createOutputModel(CloudOutputController(self)))

        for model, printer in updated_printers:
            printer.updateOutputModel(model)

        # Always have an active printer
        if self._printers and not self._active_printer:
            self.setActivePrinter(self._printers[0])

        if added_printers or removed_printers:
            self.printersChanged.emit()

    ## Updates the local list of print jobs with the list received from the cloud.
    #  \param jobs: The print jobs received from the cloud.
    def _updatePrintJobs(self, jobs: List[CloudClusterPrintJobStatus]) -> None:
        received = {j.uuid: j for j in jobs}  # type: Dict[str, CloudClusterPrintJobStatus]
        previous = {j.key: j for j in self._print_jobs}  # type: Dict[str, UM3PrintJobOutputModel]

        removed_jobs, added_jobs, updated_jobs = findChanges(previous, received)

        for removed_job in removed_jobs:
            if removed_job.assignedPrinter:
                removed_job.assignedPrinter.updateActivePrintJob(None)
                removed_job.stateChanged.disconnect(self._onPrintJobStateChanged)
            self._print_jobs.remove(removed_job)

        for added_job in added_jobs:
            self._addPrintJob(added_job)

        for model, job in updated_jobs:
            job.updateOutputModel(model)
            if job.printer_uuid:
                self._updateAssignedPrinter(model, job.printer_uuid)

        # We only have to update when jobs are added or removed
        # updated jobs push their changes via their output model
        if added_jobs or removed_jobs:
            self.printJobsChanged.emit()

    ## Registers a new print job received via the cloud API.
    #  \param job: The print job received.
    def _addPrintJob(self, job: CloudClusterPrintJobStatus) -> None:
        model = job.createOutputModel(CloudOutputController(self))
        model.stateChanged.connect(self._onPrintJobStateChanged)
        if job.printer_uuid:
            self._updateAssignedPrinter(model, job.printer_uuid)
        self._print_jobs.append(model)

    ## Handles the event of a change in a print job state
    def _onPrintJobStateChanged(self) -> None:
        user_name = self._getUserName()
        # TODO: confirm that notifications in Cura are still required
        for job in self._print_jobs:
            if job.state == "wait_cleanup" and job.key not in self._finished_jobs and job.owner == user_name:
                self._finished_jobs.add(job.key)
                Message(
                    title = I18N_CATALOG.i18nc("@info:status", "Print finished"),
                    text = (I18N_CATALOG.i18nc("@info:status", "Printer '{printer_name}' has finished printing '{job_name}'.").format(
                        printer_name = job.assignedPrinter.name,
                        job_name = job.name
                    ) if job.assignedPrinter else
                            I18N_CATALOG.i18nc("@info:status", "The print job '{job_name}' was finished.").format(
                                job_name = job.name
                            )),
                ).show()

    ## Updates the printer assignment for the given print job model.
    def _updateAssignedPrinter(self, model: UM3PrintJobOutputModel, printer_uuid: str) -> None:
        printer = next((p for p in self._printers if printer_uuid == p.key), None)
        if not printer:
            Logger.log("w", "Missing printer %s for job %s in %s", model.assignedPrinter, model.key,
                            [p.key for p in self._printers])
            return

        printer.updateActivePrintJob(model)
        model.updateAssignedPrinter(printer)

    ## Uploads the mesh when the print job was registered with the cloud API.
    #  \param job_response: The response received from the cloud API.
    def _onPrintJobCreated(self, job_response: CloudPrintJobResponse) -> None:
        self._progress.show()
        self._uploaded_print_job = job_response
        tool_path = cast(bytes, self._tool_path)
        self._api.uploadToolPath(job_response, tool_path, self._onPrintJobUploaded, self._progress.update, self._onUploadError)

    ## Requests the print to be sent to the printer when we finished uploading the mesh.
    def _onPrintJobUploaded(self) -> None:
        self._progress.update(100)
        print_job = cast(CloudPrintJobResponse, self._uploaded_print_job)
        self._api.requestPrint(self.key, print_job.job_id, self._onPrintUploadCompleted)

    ## Displays the given message if uploading the mesh has failed
    #  \param message: The message to display.
    def _onUploadError(self, message: str = None) -> None:
        self._progress.hide()
        self._uploaded_print_job = None
        Message(
            text = message or I18N_CATALOG.i18nc("@info:text", "Could not upload the data to the printer."),
            title = I18N_CATALOG.i18nc("@info:title", "Cloud error"),
            lifetime = 10
        ).show()
        self.writeError.emit()

    ## Shows a message when the upload has succeeded
    #  \param response: The response from the cloud API.
    def _onPrintUploadCompleted(self, response: CloudPrintResponse) -> None:
        Logger.log("d", "The cluster will be printing this print job with the ID %s", response.cluster_job_id)
        self._progress.hide()
        Message(
            text = I18N_CATALOG.i18nc("@info:status", "Print job was successfully sent to the printer."),
            title = I18N_CATALOG.i18nc("@info:title", "Data Sent"),
            lifetime = 5
        ).show()
        self.writeFinished.emit()

    ##  Whether the printer that this output device represents supports print job actions via the cloud.
    @pyqtProperty(bool, notify = _clusterPrintersChanged)
    def supportsPrintJobActions(self) -> bool:
        version_number = self.printers[0].firmwareVersion.split(".")
        firmware_version = Version([version_number[0], version_number[1], version_number[2]])
        return firmware_version >= self.PRINT_JOB_ACTIONS_MIN_VERSION

    ##  Gets the number of printers in the cluster.
    #   We use a minimum of 1 because cloud devices are always a cluster and printer discovery needs it.
    @pyqtProperty(int, notify = _clusterPrintersChanged)
    def clusterSize(self) -> int:
        return max(1, len(self._printers))

    ##  Gets the remote printers.
    @pyqtProperty("QVariantList", notify=_clusterPrintersChanged)
    def printers(self) -> List[PrinterOutputModel]:
        return self._printers

    ##  Get the active printer in the UI (monitor page).
    @pyqtProperty(QObject, notify = activePrinterChanged)
    def activePrinter(self) -> Optional[PrinterOutputModel]:
        return self._active_printer

    ## Set the active printer in the UI (monitor page).
    @pyqtSlot(QObject)
    def setActivePrinter(self, printer: Optional[PrinterOutputModel] = None) -> None:
        if printer != self._active_printer:
            self._active_printer = printer
            self.activePrinterChanged.emit()

    ##  Get remote print jobs.
    @pyqtProperty("QVariantList", notify = printJobsChanged)
    def printJobs(self) -> List[UM3PrintJobOutputModel]:
        return self._print_jobs

    ##  Get remote print jobs that are still in the print queue.
    @pyqtProperty("QVariantList", notify = printJobsChanged)
    def queuedPrintJobs(self) -> List[UM3PrintJobOutputModel]:
        return [print_job for print_job in self._print_jobs
                if print_job.state == "queued" or print_job.state == "error"]

    ##  Get remote print jobs that are assigned to a printer.
    @pyqtProperty("QVariantList", notify = printJobsChanged)
    def activePrintJobs(self) -> List[UM3PrintJobOutputModel]:
        return [print_job for print_job in self._print_jobs if
                print_job.assignedPrinter is not None and print_job.state != "queued"]

    def setJobState(self, print_job_uuid: str, state: str) -> None:
        self._api.doPrintJobAction(self._cluster.cluster_id, print_job_uuid, state)

    @pyqtSlot(str)
    def sendJobToTop(self, print_job_uuid: str) -> None:
        self._api.doPrintJobAction(self._cluster.cluster_id, print_job_uuid, "move",
                                   {"list": "queued", "to_position": 0})

    @pyqtSlot(str)
    def deleteJobFromQueue(self, print_job_uuid: str) -> None:
        self._api.doPrintJobAction(self._cluster.cluster_id, print_job_uuid, "remove")

    @pyqtSlot(str)
    def forceSendJob(self, print_job_uuid: str) -> None:
        self._api.doPrintJobAction(self._cluster.cluster_id, print_job_uuid, "force")

    @pyqtSlot(int, result = str)
    def formatDuration(self, seconds: int) -> str:
        return Duration(seconds).getDisplayString(DurationFormat.Format.Short)

    @pyqtSlot(int, result = str)
    def getTimeCompleted(self, time_remaining: int) -> str:
        return formatTimeCompleted(time_remaining)

    @pyqtSlot(int, result = str)
    def getDateCompleted(self, time_remaining: int) -> str:
        return formatDateCompleted(time_remaining)

    @pyqtProperty(bool, notify=printJobsChanged)
    def receivedPrintJobs(self) -> bool:
        return bool(self._print_jobs)

    @pyqtSlot()
    def openPrintJobControlPanel(self) -> None:
        QDesktopServices.openUrl(QUrl("https://mycloud.ultimaker.com"))

    @pyqtSlot()
    def openPrinterControlPanel(self) -> None:
        QDesktopServices.openUrl(QUrl("https://mycloud.ultimaker.com"))

    ##  TODO: The following methods are required by the monitor page QML, but are not actually available using cloud.
    #   TODO: We fake the methods here to not break the monitor page.

    @pyqtProperty(QUrl, notify = _clusterPrintersChanged)
    def activeCameraUrl(self) -> "QUrl":
        return QUrl()

    @pyqtSlot(QUrl)
    def setActiveCameraUrl(self, camera_url: "QUrl") -> None:
        pass

    @pyqtProperty("QVariantList", notify = _clusterPrintersChanged)
    def connectedPrintersTypeCount(self) -> List[Dict[str, str]]:
        return []
