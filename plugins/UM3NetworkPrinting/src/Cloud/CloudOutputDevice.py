# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
import os
from datetime import datetime

from time import time
from typing import Dict, List, Optional, Set

from PyQt5.QtCore import QObject, QUrl, pyqtProperty, pyqtSignal, pyqtSlot

from UM import i18nCatalog
from UM.FileHandler.FileHandler import FileHandler
from UM.Logger import Logger
from UM.Message import Message
from UM.Qt.Duration import Duration, DurationFormat
from UM.Scene.SceneNode import SceneNode
from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.NetworkedPrinterOutputDevice import AuthState, NetworkedPrinterOutputDevice
from cura.PrinterOutput.PrinterOutputController import PrinterOutputController
from cura.PrinterOutput.PrinterOutputModel import PrinterOutputModel
from plugins.UM3NetworkPrinting.src.Cloud.CloudOutputController import CloudOutputController
from ..MeshFormatHandler import MeshFormatHandler
from ..UM3PrintJobOutputModel import UM3PrintJobOutputModel
from .CloudApiClient import CloudApiClient
from .Models.CloudClusterStatus import CloudClusterStatus
from .Models.CloudJobUploadRequest import CloudJobUploadRequest
from .Models.CloudPrintResponse import CloudPrintResponse
from .Models.CloudJobResponse import CloudJobResponse
from .Models.CloudClusterPrinter import CloudClusterPrinter
from .Models.CloudClusterPrintJob import CloudClusterPrintJob
from .Utils import findChanges


## Class that contains all the translations for this module.
class T:
    # The translation catalog for this device.

    _I18N_CATALOG = i18nCatalog("cura")

    PRINT_VIA_CLOUD_BUTTON = _I18N_CATALOG.i18nc("@action:button", "Print via Cloud")
    PRINT_VIA_CLOUD_TOOLTIP = _I18N_CATALOG.i18nc("@properties:tooltip", "Print via Cloud")

    CONNECTED_VIA_CLOUD = _I18N_CATALOG.i18nc("@info:status", "Connected via Cloud")
    BLOCKED_UPLOADING = _I18N_CATALOG.i18nc("@info:status", "Sending new jobs (temporarily) blocked, still sending "
                                                            "the previous print job.")

    COULD_NOT_EXPORT = _I18N_CATALOG.i18nc("@info:status", "Could not export print job.")

    SENDING_DATA_TEXT = _I18N_CATALOG.i18nc("@info:status", "Sending data to remote cluster")
    SENDING_DATA_TITLE = _I18N_CATALOG.i18nc("@info:status", "Sending data to remote cluster")

    ERROR = _I18N_CATALOG.i18nc("@info:title", "Error")
    UPLOAD_ERROR = _I18N_CATALOG.i18nc("@info:text", "Could not upload the data to the printer.")

    UPLOAD_SUCCESS_TITLE = _I18N_CATALOG.i18nc("@info:title", "Data Sent")
    UPLOAD_SUCCESS_TEXT = _I18N_CATALOG.i18nc("@info:status", "Print job was successfully sent to the printer.")


##  The cloud output device is a network output device that works remotely but has limited functionality.
#   Currently it only supports viewing the printer and print job status and adding a new job to the queue.
#   As such, those methods have been implemented here.
#   Note that this device represents a single remote cluster, not a list of multiple clusters.
#
#   TODO: figure our how the QML interface for the cluster networking should operate with this limited functionality.
class CloudOutputDevice(NetworkedPrinterOutputDevice):

    # The interval with which the remote clusters are checked
    CHECK_CLUSTER_INTERVAL = 2.0  # seconds

    # Signal triggered when the print jobs in the queue were changed.
    printJobsChanged = pyqtSignal()

    # Signal triggered when the selected printer in the UI should be changed.
    activePrinterChanged = pyqtSignal()

    # Notify can only use signals that are defined by the class that they are in, not inherited ones.
    # Therefore we create a private signal used to trigger the printersChanged signal.
    _clusterPrintersChanged = pyqtSignal()

    ## Creates a new cloud output device
    #  \param api_client: The client that will run the API calls
    #  \param device_id: The ID of the device (i.e. the cluster_id for the cloud API)
    #  \param parent: The optional parent of this output device.
    def __init__(self, api_client: CloudApiClient, device_id: str, host_name: str, parent: QObject = None) -> None:
        super().__init__(device_id = device_id, address = "", properties = {}, parent = parent)
        self._api = api_client
        self._host_name = host_name

        self._setInterfaceElements()
        
        self._device_id = device_id
        self._account = CuraApplication.getInstance().getCuraAPI().account

        # We use the Cura Connect monitor tab to get most functionality right away.
        self._monitor_view_qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "../../resources/qml/ClusterMonitorItem.qml")
        self._control_view_qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "../../resources/qml/ClusterControlItem.qml")

        # Trigger the printersChanged signal when the private signal is triggered.
        self.printersChanged.connect(self._clusterPrintersChanged)

        # We keep track of which printer is visible in the monitor page.
        self._active_printer = None  # type: Optional[PrinterOutputModel]

        # Properties to populate later on with received cloud data.
        self._print_jobs = []  # type: List[UM3PrintJobOutputModel]
        self._number_of_extruders = 2  # All networked printers are dual-extrusion Ultimaker machines.
        
        # We only allow a single upload at a time.
        self._sending_job = False
        self._progress_message = None  # type: Optional[Message]

    ## Gets the host name of this device
    @property
    def host_name(self) -> str:
        return self._host_name

    ## Updates the host name of the output device
    @host_name.setter
    def host_name(self, value: str) -> None:
        self._host_name = value

    ## Checks whether the given network key is found in the cloud's host name
    def matchesNetworkKey(self, network_key: str) -> bool:
        # A network key looks like "ultimakersystem-aabbccdd0011._ultimaker._tcp.local."
        # the host name should then be "ultimakersystem-aabbccdd0011"
        return network_key.startswith(self._host_name)

    ##  Set all the interface elements and texts for this output device.
    def _setInterfaceElements(self):
        self.setPriority(2)  # make sure we end up below the local networking and above 'save to file'
        self.setName(self._id)
        self.setShortDescription(T.PRINT_VIA_CLOUD_BUTTON)
        self.setDescription(T.PRINT_VIA_CLOUD_TOOLTIP)
        self.setConnectionText(T.CONNECTED_VIA_CLOUD)
    
    ##  Called when Cura requests an output device to receive a (G-code) file.
    def requestWrite(self, nodes: List[SceneNode], file_name: Optional[str] = None, limit_mime_types: bool = False,
                     file_handler: Optional[FileHandler] = None, **kwargs: str) -> None:
        
        # Show an error message if we're already sending a job.
        if self._sending_job:
            self._onUploadError(T.BLOCKED_UPLOADING)
            return
        
        # Indicate we have started sending a job.
        self._sending_job = True
        self.writeStarted.emit(self)

        mesh_format = MeshFormatHandler(file_handler, self.firmwareVersion)
        if not mesh_format.is_valid:
            Logger.log("e", "Missing file or mesh writer!")
            return self._onUploadError(T.COULD_NOT_EXPORT)

        mesh_bytes = mesh_format.getBytes(nodes)

        # TODO: Remove extension from the file name, since we are using content types now
        request = CloudJobUploadRequest(
            job_name = file_name + "." + mesh_format.file_extension,
            file_size = len(mesh_bytes),
            content_type = mesh_format.mime_type,
        )
        self._api.requestUpload(request, lambda response: self._onPrintJobCreated(mesh_bytes, response))

    ##  Get remote printers.
    @pyqtProperty("QVariantList", notify = _clusterPrintersChanged)
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

    @pyqtProperty(int, notify = _clusterPrintersChanged)
    def clusterSize(self) -> int:
        return len(self._printers)

    ##  Get remote print jobs.
    @pyqtProperty("QVariantList", notify = printJobsChanged)
    def printJobs(self)-> List[UM3PrintJobOutputModel]:
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

    @pyqtSlot(int, result = str)
    def formatDuration(self, seconds: int) -> str:
        # TODO: this really shouldn't be in this class
        return Duration(seconds).getDisplayString(DurationFormat.Format.Short)

    @pyqtSlot(int, result = str)
    def getTimeCompleted(self, time_remaining: int) -> str:
        # TODO: this really shouldn't be in this class
        current_time = time()
        datetime_completed = datetime.fromtimestamp(current_time + time_remaining)
        return "{hour:02d}:{minute:02d}".format(hour = datetime_completed.hour, minute = datetime_completed.minute)

    @pyqtSlot(int, result = str)
    def getDateCompleted(self, time_remaining: int) -> str:
        # TODO: this really shouldn't be in this class
        current_time = time()
        completed = datetime.fromtimestamp(current_time + time_remaining)
        today = datetime.fromtimestamp(current_time)
        # If finishing date is more than 7 days out, using "Mon Dec 3 at HH:MM" format
        if completed.toordinal() > today.toordinal() + 7:
            return completed.strftime("%a %b ") + "{day}".format(day = completed.day)
        # If finishing date is within the next week, use "Monday at HH:MM" format
        elif completed.toordinal() > today.toordinal() + 1:
            return completed.strftime("%a")
        # If finishing tomorrow, use "tomorrow at HH:MM" format
        elif completed.toordinal() > today.toordinal():
            return "tomorrow"
        # If finishing today, use "today at HH:MM" format
        else:
            return "today"

    ##  Called when the connection to the cluster changes.
    def connect(self) -> None:
        super().connect()

    ##  Called when the network data should be updated.
    def _update(self) -> None:
        super()._update()
        if self._last_response_time and time() - self._last_response_time < self.CHECK_CLUSTER_INTERVAL:
            return  # avoid calling the cloud too often

        if self._account.isLoggedIn:
            self.setAuthenticationState(AuthState.Authenticated)
            self._api.getClusterStatus(self._device_id, self._onStatusCallFinished)
        else:
            self.setAuthenticationState(AuthState.NotAuthenticated)

    ##  Method called when HTTP request to status endpoint is finished.
    #   Contains both printers and print jobs statuses in a single response.
    def _onStatusCallFinished(self, status: CloudClusterStatus) -> None:
        # Update all data from the cluster.
        self._updatePrinters(status.printers)
        self._updatePrintJobs(status.print_jobs)

    def _updatePrinters(self, printers: List[CloudClusterPrinter]) -> None:
        previous = {p.key: p for p in self._printers}  # type: Dict[str, PrinterOutputModel]
        received = {p.uuid: p for p in printers}  # type: Dict[str, CloudClusterPrinter]

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
        if not self._active_printer:
            self.setActivePrinter(self._printers[0])

        if removed_printers or added_printers or updated_printers:
            self._clusterPrintersChanged.emit()

    def _updatePrintJobs(self, jobs: List[CloudClusterPrintJob]) -> None:
        received = {j.uuid: j for j in jobs}  # type: Dict[str, CloudClusterPrintJob]
        previous = {j.key: j for j in self._print_jobs}  # type: Dict[str, UM3PrintJobOutputModel]

        removed_jobs, added_jobs, updated_jobs = findChanges(previous, received)

        # TODO: we see that not all data in the UI is correctly updated when the queue and active jobs change.
        # TODO: we need to fix this here somehow by updating the correct output models.
        # TODO: also the configuration drop down in the slice window is not populated because we are missing some data.
        # TODO: to fix this we need to implement more data as shown in ClusterUM3OutputDevice._createPrintJobModel

        for removed_job in removed_jobs:
            self._print_jobs.remove(removed_job)

        for added_job in added_jobs:
            self._addPrintJob(added_job)

        for model, job in updated_jobs:
            job.updateOutputModel(model)
            self._updatePrintJobDetails(model)

        # We only have to update when jobs are added or removed
        # updated jobs push their changes via their output model
        if added_jobs or removed_jobs or updated_jobs:
            self.printJobsChanged.emit()

    def _addPrintJob(self, job: CloudClusterPrintJob) -> None:
        print_job = job.createOutputModel(CloudOutputController(self))
        self._updatePrintJobDetails(print_job)
        self._print_jobs.append(print_job)

    def _updatePrintJobDetails(self, print_job: UM3PrintJobOutputModel):
        printer = None
        try:
            printer = next(p for p in self._printers if print_job.assignedPrinter == p.key)
        except StopIteration:
            Logger.log("w", "Missing printer %s for job %s in %s", print_job.assignedPrinter, print_job.key,
                       [p.key for p in self._printers])

        if printer:
            printer.updateActivePrintJob(print_job)
            print_job.updateAssignedPrinter(printer)

    def _onPrintJobCreated(self, mesh: bytes, job_response: CloudJobResponse) -> None:
        self._api.uploadMesh(job_response, mesh, self._onPrintJobUploaded, self._updateUploadProgress,
                             lambda _: self._onUploadError(T.UPLOAD_ERROR))

    def _onPrintJobUploaded(self, job_id: str) -> None:
        self._api.requestPrint(self._device_id, job_id, self._onUploadSuccess)

    def _updateUploadProgress(self, progress: int):
        if not self._progress_message:
            self._progress_message = Message(
                text = T.SENDING_DATA_TEXT,
                title = T.SENDING_DATA_TITLE,
                progress = -1,
                lifetime = 0,
                dismissable = False,
                use_inactivity_timer = False
            )
        self._progress_message.setProgress(progress)
        self._progress_message.show()

    def _resetUploadProgress(self):
        if self._progress_message:
            self._progress_message.hide()
            self._progress_message = None

    def _onUploadError(self, message: str = None):
        self._resetUploadProgress()
        if message:
            message = Message(
                text = message,
                title = T.ERROR,
                lifetime = 10,
                dismissable = True
            )
            message.show()
        self._sending_job = False  # the upload has finished so we're not sending a job anymore
        self.writeError.emit()

    # Shows a message when the upload has succeeded
    def _onUploadSuccess(self, response: CloudPrintResponse):
        Logger.log("i", "The cluster will be printing this print job with the ID %s", response.cluster_job_id)
        self._resetUploadProgress()
        message = Message(
            text = T.UPLOAD_SUCCESS_TEXT,
            title = T.UPLOAD_SUCCESS_TITLE,
            lifetime = 5,
            dismissable = True,
        )
        message.show()
        self._sending_job = False  # the upload has finished so we're not sending a job anymore
        self.writeFinished.emit()

    ##  TODO: The following methods are required by the monitor page QML, but are not actually available using cloud.
    #   TODO: We fake the methods here to not break the monitor page.

    @pyqtProperty(QUrl, notify = _clusterPrintersChanged)
    def activeCameraUrl(self) -> "QUrl":
        return QUrl()

    @pyqtSlot(QUrl)
    def setActiveCameraUrl(self, camera_url: "QUrl") -> None:
        pass

    @pyqtProperty(bool, notify = printJobsChanged)
    def receivedPrintJobs(self) -> bool:
        return True

    @pyqtSlot()
    def openPrintJobControlPanel(self) -> None:
        pass

    @pyqtSlot()
    def openPrinterControlPanel(self) -> None:
        pass

    @pyqtSlot(str)
    def sendJobToTop(self, print_job_uuid: str) -> None:
        pass

    @pyqtSlot(str)
    def deleteJobFromQueue(self, print_job_uuid: str) -> None:
        pass

    @pyqtSlot(str)
    def forceSendJob(self, print_job_uuid: str) -> None:
        pass

    @pyqtProperty("QVariantList", notify = _clusterPrintersChanged)
    def connectedPrintersTypeCount(self) -> List[Dict[str, str]]:
        return []
